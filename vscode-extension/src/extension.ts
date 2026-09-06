import * as vscode from "vscode";
import { spawn, ChildProcessWithoutNullStreams } from "node:child_process";

let bridgeProcess: ChildProcessWithoutNullStreams | undefined;

function workspacePath(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel("Ruata AI");
  const config = vscode.workspace.getConfiguration("ruata");

  context.subscriptions.push(
    vscode.commands.registerCommand("ruata.connect", async () => {
      const workspace = workspacePath();
      if (!workspace) {
        void vscode.window.showErrorMessage("Ruata: open a project workspace first.");
        return;
      }
      const url = config.get<string>("controlPlaneUrl", "ws://localhost:8000/ws/bridge");
      const token = config.get<string>("bridgeToken", "");
      const python = config.get<string>("pythonPath", "python");
      if (!token) {
        void vscode.window.showWarningMessage("Ruata: configure ruata.bridgeToken before connecting.");
        return;
      }
      if (bridgeProcess) {
        void vscode.window.showInformationMessage("Ruata: local bridge is already running.");
        return;
      }

      output.appendLine(`Starting Local Agent Bridge for ${workspace}`);
      bridgeProcess = spawn(
        python,
        ["-m", "local.bridge.main", "--workspace", workspace, "--url", url, "--token", token],
        { cwd: workspace, shell: false },
      );
      bridgeProcess.stdout.on("data", (data) => output.append(data.toString()));
      bridgeProcess.stderr.on("data", (data) => output.append(data.toString()));
      bridgeProcess.on("exit", (code) => {
        output.appendLine(`Bridge exited with code ${code ?? "unknown"}.`);
        bridgeProcess = undefined;
      });
      void vscode.window.showInformationMessage("Ruata: local bridge started.");
    }),
    vscode.commands.registerCommand("ruata.status", async () => {
      const workspace = workspacePath() ?? "none";
      output.appendLine(`Workspace: ${workspace}`);
      output.appendLine(`Bridge: ${bridgeProcess ? "running" : "stopped"}`);
      void vscode.window.showInformationMessage(`Ruata: ${bridgeProcess ? "bridge running" : "bridge stopped"}.`);
    }),
    vscode.commands.registerCommand("ruata.stop", async () => {
      bridgeProcess?.kill();
      bridgeProcess = undefined;
      void vscode.window.showInformationMessage("Ruata: local bridge stopped.");
    }),
    output,
  );
}

export function deactivate(): void {
  bridgeProcess?.kill();
  bridgeProcess = undefined;
}
