import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext): void {
  const output = vscode.window.createOutputChannel('Ruata AI');

  context.subscriptions.push(
    vscode.commands.registerCommand('ruata.connect', async () => {
      output.appendLine('Ruata local bridge connection requested.');
      void vscode.window.showInformationMessage('Ruata: local bridge scaffold is ready for connection configuration.');
    }),
    vscode.commands.registerCommand('ruata.status', async () => {
      output.appendLine(`Workspace: ${vscode.workspace.workspaceFolders?.[0]?.uri.fsPath ?? 'none'}`);
      void vscode.window.showInformationMessage('Ruata: VS Code extension is active.');
    }),
    output,
  );
}

export function deactivate(): void {}
