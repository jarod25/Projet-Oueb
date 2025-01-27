import { getMessages, state, replaceEmoji } from "./ajax_room_messages.js";

$(document).on("click", ".edit-message", function (e) {
    state.isEditing = true; // Set editing flag
    e.preventDefault();
    const button = $(this);
    const messageLine = button.closest("#message-line");
    $('.edit-message').not(button).attr("style", "display: none;"); // Cache les autres boutons
    $('.delete-message').attr("style", "display: none;");
    const messageContent = messageLine.find(".text-break").text().trim();
    messageLine.data("original-content", messageContent);
    getMessages();
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
    $('.edit-message').attr("style", "display: block;");
    $('.delete-message').attr("style", "display: block;");
});

$(document).on("click", ".save-edit-button", function (e) {
    e.preventDefault();
    const button = $(this);
    const messageLine = button.closest("#message-line");
    const messageId = messageLine.data("message-id");
    let newContent = messageLine.find(".edit-textarea").val();
    newContent = replaceEmoji(newContent)

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
            $('.edit-message').attr("style", "display: block;");
            $('.delete-message').attr("style", "display: block;");
        },
        error: function () {
            alert("Erreur lors de la modification du message.");
        }
    });
});