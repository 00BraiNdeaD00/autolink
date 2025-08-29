import vscode
from autolink.autolink import initialize_tagging, update_tags_on_file
import os


def activate(context: vscode.ExtensionContext):
    """
    This function is called when the extension is activated.
    """

    # Register a command to initialize tagging for the entire workspace.
    def init_command():
        workspace_folders = vscode.workspace.workspace_folders
        if workspace_folders:
            workspace_path = workspace_folders[0].uri.fs_path
            vscode.window.show_information_message(
                f"Running autolink initialization on: {workspace_path}"
            )
            try:
                initialize_tagging(workspace_path)
                vscode.window.show_information_message(
                    "Autolink initialization complete!"
                )
            except Exception as e:
                vscode.window.show_error_message(f"Autolink initialization failed: {e}")
        else:
            vscode.window.show_warning_message(
                "No workspace folder open to initialize autolink."
            )

    context.subscriptions.append(
        vscode.commands.register_command("autolink.initialize", init_command)
    )

    # Register a listener for when a Markdown document is saved.
    def on_save_handler(document: vscode.TextDocument):
        if document.language_id == "markdown" and not document.file_name.endswith(
            "linklist.md"
        ):
            file_path = document.uri.fs_path
            vscode.window.set_status_bar_message(
                f"Autolink: Updating tags for {os.path.basename(file_path)}...", 2000
            )
            try:
                update_tags_on_file(file_path)
                vscode.window.set_status_bar_message("Autolink: Update complete!", 2000)
            except Exception as e:
                vscode.window.show_error_message(
                    f"Autolink failed for {os.path.basename(file_path)}: {e}"
                )

    context.subscriptions.append(
        vscode.workspace.on_did_save_text_document(on_save_handler)
    )

    vscode.window.show_information_message("Autolink extension is now active!")


def deactivate():
    """
    This function is called when the extension is deactivated.
    """
    pass
