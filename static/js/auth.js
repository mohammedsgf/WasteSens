/**
 * Authentication form handler for sign in and sign up pages.
 * Submits forms via fetch, displays inline errors, redirects on success.
 */
(function () {
    "use strict";

    const signinForm = document.getElementById("signin-form");
    const signupForm = document.getElementById("signup-form");

    /**
     * Show a field-level error message.
     */
    function showFieldError(fieldId, message) {
        const errorEl = document.getElementById(fieldId + "-error");
        const inputEl = document.getElementById(fieldId);
        if (errorEl) errorEl.textContent = message;
        if (inputEl) inputEl.classList.add("input-error");
    }

    /**
     * Clear all field-level errors.
     */
    function clearErrors(form) {
        form.querySelectorAll(".field-error").forEach(el => (el.textContent = ""));
        form.querySelectorAll("input").forEach(el => el.classList.remove("input-error"));
        const formError = document.getElementById("form-error");
        if (formError) {
            formError.textContent = "";
            formError.classList.remove("visible");
        }
    }

    /**
     * Show a form-level error message.
     */
    function showFormError(message) {
        const formError = document.getElementById("form-error");
        if (formError) {
            formError.textContent = message;
            formError.classList.add("visible");
        }
    }

    /**
     * Set submit button loading state.
     */
    function setLoading(form, loading) {
        const btn = form.querySelector("#submit-btn");
        if (btn) {
            btn.disabled = loading;
            btn.textContent = loading ? "Please wait..." : btn.dataset.originalText || btn.textContent;
            if (!btn.dataset.originalText) {
                btn.dataset.originalText = btn.textContent;
            }
        }
    }

    // ---- SIGN IN ----
    if (signinForm) {
        signinForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            clearErrors(signinForm);

            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;

            // Client-side validation
            let valid = true;
            if (!email) {
                showFieldError("email", "Email is required.");
                valid = false;
            }
            if (!password) {
                showFieldError("password", "Password is required.");
                valid = false;
            }
            if (!valid) return;

            setLoading(signinForm, true);

            try {
                const res = await fetch("/api/auth/signin", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ email, password }),
                });

                const data = await res.json();

                if (res.ok) {
                    window.location.href = "/dashboard";
                } else {
                    showFormError(data.detail || "Sign in failed. Please try again.");
                }
            } catch (err) {
                showFormError("Network error. Please check your connection.");
            } finally {
                setLoading(signinForm, false);
            }
        });
    }

    // ---- SIGN UP ----
    if (signupForm) {
        signupForm.addEventListener("submit", async function (e) {
            e.preventDefault();
            clearErrors(signupForm);

            const name = document.getElementById("name").value.trim();
            const email = document.getElementById("email").value.trim();
            const password = document.getElementById("password").value;
            const confirmPassword = document.getElementById("confirm_password").value;

            // Client-side validation
            let valid = true;
            if (!name) {
                showFieldError("name", "Name is required.");
                valid = false;
            }
            if (!email) {
                showFieldError("email", "Email is required.");
                valid = false;
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
                showFieldError("email", "Please enter a valid email.");
                valid = false;
            }
            if (!password) {
                showFieldError("password", "Password is required.");
                valid = false;
            } else if (password.length < 6) {
                showFieldError("password", "Password must be at least 6 characters.");
                valid = false;
            }
            if (!confirmPassword) {
                showFieldError("confirm_password", "Please confirm your password.");
                valid = false;
            } else if (password !== confirmPassword) {
                showFieldError("confirm_password", "Passwords do not match.");
                valid = false;
            }
            if (!valid) return;

            setLoading(signupForm, true);

            try {
                const res = await fetch("/api/auth/signup", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        name,
                        email,
                        password,
                        confirm_password: confirmPassword,
                    }),
                });

                const data = await res.json();

                if (res.ok) {
                    // Redirect to sign in with success message
                    window.location.href = "/signin?registered=1";
                } else {
                    showFormError(data.detail || "Sign up failed. Please try again.");
                }
            } catch (err) {
                showFormError("Network error. Please check your connection.");
            } finally {
                setLoading(signupForm, false);
            }
        });
    }
})();
