// Pipeline editor model (fe_003): build a linear chain by dragging functions in,
// wire outputs→inputs, produce a valid pipeline manifest. v1 = sequential (no DAG).

import type { PipelineManifest, Step } from "./types";

export class PipelineEditor {
  namespace = "";
  name = "";
  steps: Step[] = [];

  private byId(id: string): Step {
    const s = this.steps.find((x) => x.id === id);
    if (!s) throw new Error(`unknown step: ${id}`);
    return s;
  }

  addStep(use: string, id?: string): string {
    const sid = id ?? `step${this.steps.length + 1}`;
    if (this.steps.some((s) => s.id === sid)) throw new Error(`duplicate step id: ${sid}`);
    this.steps.push({ id: sid, use, with: {} });
    return sid;
  }

  removeStep(id: string): void {
    this.steps = this.steps.filter((s) => s.id !== id);
  }

  move(id: string, toIndex: number): void {
    const from = this.steps.findIndex((s) => s.id === id);
    if (from < 0) throw new Error(`unknown step: ${id}`);
    const [s] = this.steps.splice(from, 1);
    this.steps.splice(Math.max(0, Math.min(toIndex, this.steps.length)), 0, s);
  }

  setLiteral(stepId: string, input: string, value: unknown): void {
    this.byId(stepId).with[input] = value;
  }

  wire(stepId: string, input: string, fromStepId: string, output: string): void {
    this.byId(fromStepId); // validates upstream exists
    this.byId(stepId).with[input] = `\${{ steps.${fromStepId}.outputs.${output} }}`;
  }

  validate(): string[] {
    const errors: string[] = [];
    if (!this.namespace) errors.push("namespace is required");
    if (!this.name) errors.push("name is required");
    if (this.steps.length === 0) errors.push("pipeline needs at least one step");
    const ids = this.steps.map((s) => s.id);
    if (new Set(ids).size !== ids.length) errors.push("step ids must be unique");
    return errors;
  }

  toManifest(): PipelineManifest {
    const errors = this.validate();
    if (errors.length) throw new Error(`invalid pipeline: ${errors.join("; ")}`);
    return {
      kind: "pipeline",
      namespace: this.namespace,
      name: this.name,
      steps: this.steps,
      flow: { mode: "standalone", end: { signal: "END" } },
    };
  }
}
