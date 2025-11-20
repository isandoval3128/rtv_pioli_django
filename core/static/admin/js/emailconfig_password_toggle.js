// admin/js/emailconfig_password_toggle.js

document.addEventListener('DOMContentLoaded', function() {
    var pwdField = document.getElementById('id_email_host_password');
    if (pwdField) {
        // Avoid duplicate button
        if (!document.getElementById('togglePwdBtn')) {
            var btn = document.createElement('button');
            btn.type = 'button';
            btn.id = 'togglePwdBtn';
            btn.textContent = 'Mostrar';
            btn.style.marginLeft = '10px';
            btn.onclick = function() {
                if (pwdField.type === 'password') {
                    pwdField.type = 'text';
                    btn.textContent = 'Ocultar';
                } else {
                    pwdField.type = 'password';
                    btn.textContent = 'Mostrar';
                }
            };
            pwdField.parentNode.appendChild(btn);
        }
    }
});
