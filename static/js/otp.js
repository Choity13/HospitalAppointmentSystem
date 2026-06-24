// static/js/otp.js
document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const otpInputs = document.querySelectorAll('.otp-input');
    const countdownEl = document.getElementById('countdown');
    const resendBtn = document.getElementById('resendBtn');
    const otpForm = document.querySelector('form[action*="verify_otp"]');
    const resendForm = document.querySelector('form[action*="resend_otp"]');
    
    let timerInterval;
    let timeLeft = 600; // 10 minutes in seconds
    
    // Initialize everything
    initOtpInputs();
    initCountdown();
    initResend();
    initFormSubmit();
    
    function initOtpInputs() {
        otpInputs.forEach((input, index) => {
            // Auto-advance on input
            input.addEventListener('input', (e) => {
                const value = e.target.value;
                // Only allow digits
                e.target.value = value.replace(/[^0-9]/g, '');
                if (e.target.value.length === 1 && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }
            });
            
            // Auto-backspace
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    otpInputs[index - 1].focus();
                }
            });
            
            // Paste handling
            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const pastedData = (e.clipboardData || window.clipboardData).getData('text');
                const digits = pastedData.replace(/[^0-9]/g, '').slice(0, 6);
                
                if (digits.length > 0) {
                    // Distribute digits across inputs
                    for (let i = 0; i < digits.length; i++) {
                        if (otpInputs[i]) {
                            otpInputs[i].value = digits[i];
                        }
                    }
                    // Focus on the next empty input or the last one
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
            countdownEl.textContent = 'OTP Expired!';
            countdownEl.style.color = '#dc3545';
            if (resendBtn) {
                resendBtn.style.display = 'block';
            }
        }
    }
    
    function updateCountdownDisplay() {
        if (!countdownEl) return;
        const minutes = Math.floor(timeLeft / 60);
        const seconds = timeLeft % 60;
        countdownEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }
    
    function initResend() {
        if (!resendForm) return;
        
        resendForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            // Send POST request to resend OTP
            try {
                const response = await fetch(resendForm.action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                });
                
                if (response.ok) {
                    // Reset timer
                    timeLeft = 600;
                    countdownEl.style.color = '#0077B6';
                    resendBtn.style.display = 'none';
                    clearInterval(timerInterval);
                    timerInterval = setInterval(updateCountdown, 1000);
                    updateCountdownDisplay();
                    
                    // Reload page to show flash message
                    window.location.reload();
                }
            } catch (error) {
                console.error('Error resending OTP:', error);
            }
        });
    }
    
    function initFormSubmit() {
        if (!otpForm) return;
        
        otpForm.addEventListener('submit', (e) => {
            // Prevent default submit
            e.preventDefault();
            
            // Join digits into a single string
            let otpCode = '';
            otpInputs.forEach(input => {
                otpCode += input.value;
            });
            
            // Create or update hidden input with otp_code
            let hiddenInput = otpForm.querySelector('input[name="otp_code"]');
            if (!hiddenInput) {
                hiddenInput = document.createElement('input');
                hiddenInput.type = 'hidden';
                hiddenInput.name = 'otp_code';
                otpForm.appendChild(hiddenInput);
            }
            hiddenInput.value = otpCode;
            
            // Now submit the form
            otpForm.submit();
        });
    }
});
