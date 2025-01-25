import {getMessages, state} from "./ajax_room_messages.js";

$(document).on("click", "#edit-message", function (e) {
    e.preventDefault();
    state.isEditing = true; // Set editing flag
    const button = $(this);
    const messageLine = button.closest("#message-line");
    const messageContent = messageLine.find(".text-break").text().trim();
    // Save original content for restoration if canceled
    messageLine.data("original-content", messageContent);
    getMessages();
    // Replace the message content with a textarea and buttons
    messageLine.find(".text-break").html(`
        <textarea class="edit-textarea form-control mb-2">${messageContent}</textarea>
        <button class="save-edit-button btn btn-sm btn-primary">Enregistrer</button>
        <button class="cancel-edit-button btn btn-sm btn-secondary">Annuler</button>
    `);
});

$(document).on("click", ".cancel-edit-button", function (e) {
    e.preventDefault();
    state.isEditing = false; // Reset editing flag
    const messageLine = $(this).closest("#message-line");
    const originalContent = messageLine.data("original-content");

    // Restore the original content
    messageLine.find(".text-break").text(originalContent);
});

$(document).on("click", ".save-edit-button", function (e) {
    e.preventDefault();
    const button = $(this);
    const messageLine = button.closest("#message-line");
    const messageId = messageLine.data("message-id");
    const newContent = messageLine.find(".edit-textarea").val();

    $.ajax({
        url: `/room/${messageId}/edit-message/`,
        type: "POST",
        data: {
            csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
            content: newContent,
        },
        success: function (response) {
            state.isEditing = false;
            messageLine.find(".text-break").text(response.content);
            getMessages()
        },
        error: function () {
            alert("Erreur lors de la modification du message.");
        }
    });
});