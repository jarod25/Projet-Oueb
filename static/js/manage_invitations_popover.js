$(document).ready(function () {
    function closeAllPopovers() {
        $('.popover').remove();
    }

    $('#invitationPopover').on('click', function (e) {
        e.preventDefault();
        const $trigger = $(this);
        const $invitationItem = $trigger.find('#invitation-btn');
        closeAllPopovers();
        $invitationItem.addClass('active');

        $.ajax({
            url: '/room/invitation_popover/',
            method: 'GET',
            success: function (response) {
                const $popover = $(response)
                    .addClass('popover shadow p-3')
                    .css({
                        position: 'absolute',
                        top: $trigger.offset().top,
                        left: $trigger.offset().left + $trigger.outerWidth() + 50,
                        zIndex: 1000,
                    });

                $('body').append($popover);
                let form = $popover.find('#manage-invitation-form');
                form.on('submit', function (e) {
                    e.preventDefault();
                    let $button = $(document.activeElement);
                    let invitationId = $button.data('invitation-id');
                    let value = $button.val();
                    $.ajax({
                        url: '/room/respond_to_invitation/',
                        method: 'POST',
                        data: {
                            invitation_id: invitationId,
                            response: value,
                            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').val()
                        },
                        success: function () {
                            closeAllPopovers();
                            location.reload();
                        },
                        error: function () {
                            alert('Erreur lors de la gestion des invitations.');
                        }
                    });
                });
            },
            error: function () {
                alert('Erreur lors du chargement du contenu.');
            }
        });
    });

    $(document).on('click', function (e) {
        if (!$(e.target).closest('.popover, .open-user-popover').length) {
            closeAllPopovers();
        }
    });
});