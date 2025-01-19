$(document).ready(function () {
    $('.invite-user-btn').on('click', function (e) {
        e.preventDefault();
        const url = $(this).attr('href');
        $.get(url, function (data) {
            $('#inviteUserModal .modal-body').html(data);
            $('#inviteUserModal').modal('show');
        }).fail(function () {
            alert('Erreur lors du chargement. Veuillez réessayer.');
        });
    });
});