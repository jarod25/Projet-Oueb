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

            },
            error: function () {
                alert('Erreur lors du chargement du contenu.');
            }
        });
    });

});