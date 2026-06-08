// Function creator/editor (fe_004): scaffold a function per runtime + the test command.

export interface Scaffold {
  manifest: Record<string, unknown>;
  files: Record<string, string>;
  testCommand: string[];
}

interface Template {
  entrypoint: string;
  body: string;
}

export const RUNTIME_TEMPLATES: Record<string, Template> = {
  bash: { entrypoint: "run.sh", body: 'echo "hello"\nprintf \'{}\' > "$FN_OUTPUTS"\n' },
  python: {
    entrypoint: "main.py",
    body: 'import json, os\njson.dump({}, open(os.environ["FN_OUTPUTS"], "w"))\n',
  },
  claude: { entrypoint: "prompt.md", body: "You are a function. Do the task.\n" },
  custom: { entrypoint: "Makefile", body: "run:\n\t@echo hello\n" },
};

export class FunctionCreator {
  scaffold(runtime: string, namespace: string, name: string): Scaffold {
    const tpl = RUNTIME_TEMPLATES[runtime];
    if (!tpl) throw new Error(`unknown runtime: ${runtime}`);
    if (!namespace || !name) throw new Error("namespace and name are required");
    const manifest = {
      apiVersion: "functions/v1",
      kind: "function",
      namespace,
      name,
      version: "0.0.1",
      runtime,
      entrypoint: tpl.entrypoint,
    };
    return {
      manifest,
      files: {
        [tpl.entrypoint]: tpl.body,
        "README.md": `# ${namespace}/${name}\n`,
        "i18n/en.json": JSON.stringify({ name }, null, 2) + "\n",
      },
      testCommand: ["make", "test"],
    };
  }
}
