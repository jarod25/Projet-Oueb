import {getMessages} from "./ajax_room_messages.js";

$(document).on("click", ".delete-message", function (e) {
    e.preventDefault();
    const button = $(this);
    const messageLine = button.closest("#message-line");
    const messageId = messageLine.data("message-id");

    if (messageId) {
        $.ajax({
            url: `/room/${messageId}/delete-message/`,
            type: "POST",
            data: {
                csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
            },
            success: function () {
                messageLine.remove();
            },
            error: function () {
                alert("Une erreur s'est produite lors de la suppression du message.");
            },
        });
    }
});
