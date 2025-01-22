$(document).ready(function () {
    $(document).on('input', '#receiver', function () {
        let query = $(this).val();
        let roomId = $(this).closest('form').data('room-id');
        let infos = $('#infos');
        if (query.length > 1) {
            $.ajax({
                url: `/room/${roomId}/invite/search_users`,
                data: {'q': query},
                success: function (data) {
                    let suggestionsList = $('#suggestions-list');
                    suggestionsList.empty();
                    if (data.length > 0) {
                        data.forEach(function (user) {
                            suggestionsList.append(`
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    ${user.username}
                                    <button class="btn btn-primary btn-sm invite-btn" data-user-id="${user.id}">Inviter</button>
                                </li>
                            `);
                        });
                    } else {
                        suggestionsList.append('<li class="list-group-item text-muted">Aucun utilisateur trouvé</li>');
                    }
                },
                error: function () {
                    infos.text('Erreur lors de la recherche des utilisateurs.');
                    infos.removeClass('text-success').addClass('text-danger');
                }
            });
        } else {
            $('#suggestions-list').empty();
        }
    });
});