// Settings model (fe_005): global env, secrets (write-only), folders.
// Secret VALUES are never retained client-side — only names are tracked; values are
// handed to the persister and dropped (the orchestrator's vault owns them).

export interface SettingsPayload {
  env: Record<string, string>;
  secretNames: string[];
  folders: string[];
}

export type Persister = (payload: {
  env: Record<string, string>;
  secrets: Record<string, string>;
  folders: string[];
}) => Promise<void>;

export class SettingsModel {
  env: Record<string, string> = {};
  folders: string[] = [];
  private secretNames = new Set<string>();
  private pendingSecrets: Record<string, string> = {};

  setEnv(key: string, value: string): void {
    this.env[key] = value;
  }

  setSecret(name: string, value: string): void {
    this.secretNames.add(name);
    this.pendingSecrets[name] = value; // staged for save, then cleared
  }

  addFolder(path: string): void {
    if (!this.folders.includes(path)) this.folders.push(path);
  }

  /** What the UI may display — never secret values. */
  view(): SettingsPayload {
    return { env: { ...this.env }, secretNames: [...this.secretNames], folders: [...this.folders] };
  }

  async save(persist: Persister): Promise<void> {
    await persist({ env: { ...this.env }, secrets: { ...this.pendingSecrets }, folders: [...this.folders] });
    this.pendingSecrets = {}; // values dropped after persisting
  }

  hasPendingSecretValues(): boolean {
    return Object.keys(this.pendingSecrets).length > 0;
  }
}
