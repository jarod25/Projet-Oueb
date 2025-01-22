$(document).ready(function () {
    $('.create-room-btn').on('click', function (e) {
        e.preventDefault();
        const url = $(this).attr('href');
        $.get(url, function (data) {
            $('#createRoomModal .modal-body').html(data);
            $('#createRoomModal').modal('show');
        }).fail(function () {
            alert('Erreur lors du chargement. Veuillez réessayer.');
        });
    });
});