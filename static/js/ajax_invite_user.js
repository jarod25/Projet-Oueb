$(document).ready(function () {
    $(document).on('click', '.invite-btn', function (e) {
        e.preventDefault();
        let userId = $(this).data('user-id');
        let roomId = $(this).closest('form').data('room-id');
        let infos = $('#infos');

        $.ajax({
            url: `/room/${roomId}/invite/`,
            method: 'POST',
            headers: {'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()},
            data: {
                'receiver_id': userId
            },
            success: function (response) {
                infos.text(response.message);
                infos.removeClass('text-danger').addClass('text-success');
            },
            error: function (xhr) {
                let errorMsg = xhr.responseJSON?.error || 'Erreur lors de l\'invitation.';
                infos.text(errorMsg);
                infos.removeClass('text-success').addClass('text-danger');
            }
        });
    });
});