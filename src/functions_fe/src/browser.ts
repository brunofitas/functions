// Function & pipeline browser view-model (fe_002): load + search/filter.

import type { ApiClient } from "./api";
import type { FunctionEntry } from "./types";

export class FunctionBrowser {
  all: FunctionEntry[] = [];
  query = "";
  runtime: string | null = null;

  constructor(private api: ApiClient) {}

  async load(): Promise<void> {
    this.all = await this.api.listFunctions();
  }

  runtimes(): string[] {
    return [...new Set(this.all.map((e) => e.runtime))].sort();
  }

  filtered(): FunctionEntry[] {
    const q = this.query.toLowerCase();
    return this.all.filter(
      (e) =>
        (!q || e.ref_id.toLowerCase().includes(q)) &&
        (!this.runtime || e.runtime === this.runtime),
    );
  }
}
