// import './main'

// // $(document).on("click", "#delete-message", function (e) {
//     e.preventDefault();
//     const button = $(this);
//     const messagSeLine = button.closest("#message-line");
//     const messageId = messageLine.data("message-id");

//     if (messageId) {
//         $.ajax({
//             url: `/room/${messageId}/delete-message/`,
//             type: "POST",
//             data: {
//                 csrfmiddlewaretoken: $("input[name='csrfmiddlewaretoken']").val(),
//             },
//             success: function () {
//                 setTimeout(getMessages, 1000);
//                 messageLine.remove();
//                 getMessages()
//             },
//             error: function () {
//                 alert("Une erreur s'est produite lors de la suppression du message.");
//             },
//         });
//     }
// });
