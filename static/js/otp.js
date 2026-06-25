// static/js/otp.js
document.addEventListener('DOMContentLoaded', function () {

    const otpInputs = document.querySelectorAll('.otp-input');
    const countdownEl = document.getElementById('countdown');
    const resendBtn = document.getElementById('resendBtn');

    // ── FIX: match BOTH hyphen and underscore in the URL ──────────────────
    const otpForm = document.querySelector('form[action*="verify"]');
    const resendForm = document.querySelector('form[action*="resend"]');

    let timerInterval;
    let timeLeft = 600; // 10 minutes in seconds

    initOtpInputs();
    initCountdown();
    initResend();
    initFormSubmit();

    function initOtpInputs() {
        otpInputs.forEach((input, index) => {

            input.addEventListener('input', (e) => {
                e.target.value = e.target.value.replace(/[^0-9]/g, '');
                if (e.target.value.length === 1 && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }
            });

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    otpInputs[index - 1].focus();
                }
            });

            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const pastedData = (e.clipboardData || window.clipboardData).getData('text');
                const digits = pastedData.replace(/[^0-9]/g, '').slice(0, 6);
                if (digits.length > 0) {
                    for (let i = 0; i < digits.length; i++) {
                        if (otpInputs[i]) otpInputs[i].value = digits[i];
                    }
                    const nextIndex = Math.min(digits.length, otpInputs.length - 1);
                    otpInputs[nextIndex].focus();
                }
            });
        });
    }

    function initCountdown() {
        updateCountdownDisplay();
        timerInterval = setInterval(updateCountdown, 1000);
    }

    function updateCountdown() {
        timeLeft--;
        updateCountdownDisplay();
        if (timeLeft <= 0) {
            clearInterval(timerInterval);
            if (countdownEl) {
                countdownEl.textContent = 'OTP Expired!';
                countdownEl.style.color = '#dc3545';
            }
            if (resendBtn) resendBtn.style.display = 'block';
        }
    }

    function updateCountdownDisplay() {
        if (!countdownEl) return;
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        countdownEl.textContent =
            String(minutes).padStart(2, '0') + ':' + String(seconds).padStart(2, '0');
    }

    function initResend() {
        if (!resendForm) return;
        resendForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch(resendForm.action, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                });
                if (response.ok) {
                    timeLeft = 600;
                    if (countdownEl) countdownEl.style.color = '#0077B6';
                    if (resendBtn) resendBtn.style.display = 'none';
                    clearInterval(timerInterval);
                    timerInterval = setInterval(updateCountdown, 1000);
                    updateCountdownDisplay();
                    window.location.reload();
                }
            } catch (error) {
                console.error('Error resending OTP:', error);
            }
        });
    }

    function initFormSubmit() {
        if (!otpForm) {
            console.error('OTP form not found — check that the form action contains "verify"');
            return;
        }

        otpForm.addEventListener('submit', (e) => {
            e.preventDefault();

            // Join all 6 digit boxes into one string
            let otpCode = '';
            otpInputs.forEach(input => { otpCode += input.value; });

            console.log('OTP being submitted: "' + otpCode + '" length=' + otpCode.length);

            // Write into hidden field (create it if it does not exist yet)
            let hiddenInput = otpForm.querySelector('input[name="otp_code"]');
            if (!hiddenInput) {
                hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'otp_code';
                otpForm.appendChild(hiddenInput);
            }
            hiddenInput.value = otpCode;

            otpForm.submit();
        });
    }
});
