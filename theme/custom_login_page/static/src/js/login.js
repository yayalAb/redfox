odoo.define('custom_login_page.toggle_password', [], function (require) {
    "use strict";

    $(document).ready(function() {
        
        // Use a delegated event handler attached to a static parent.
        // This is the most robust way to handle clicks.
        $('.o_login_container').on('click', '.toggle-password', function() {
            
            var $icon = $(this);
            var $passwordInput = $icon.siblings('input[name="password"]');
            
            if ($passwordInput.length) {
                if ($passwordInput.attr('type') === 'password') {
                    $passwordInput.attr('type', 'text');
                    $icon.removeClass('fa-eye-slash').addClass('fa-eye');
                } else {
                    $passwordInput.attr('type', 'password');
                    $icon.removeClass('fa-eye').addClass('fa-eye-slash');
                }
            }
        });
    });
});