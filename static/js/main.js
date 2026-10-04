/**
 * JOY2BUY - front-end behaviour (vanilla ES6, no dependencies except the
 * Bootstrap bundle already loaded on the page).
 *
 * Everything here is a progressive enhancement: each form still works with
 * a normal page reload if JavaScript is switched off.
 *
 *  1. Dismissible messages that fade out on their own
 *  2. Confirmation modal before anything is deleted
 *  3. Cart: add, change quantity and remove without reloading
 *  4. Wishlist toggle
 *  5. Live search suggestions
 *  6. Product image zoom
 *  7. Image preview on the staff product form
 *  8. Review character counter and filter auto-submit
 */
(() => {
    "use strict";

    const AJAX_HEADERS = { "X-Requested-With": "XMLHttpRequest" };
    const messageContainer = document.getElementById("message-container");

    /* ------------------------------------------------------------------
       1. Messages
       ------------------------------------------------------------------ */
    const scheduleDismiss = (alertElement) => {
        const delay = Number(alertElement.dataset.autoDismiss);
        // Errors stay on screen until the shopper closes them.
        if (!delay || alertElement.classList.contains("alert-danger")) {
            return;
        }
        window.setTimeout(() => {
            if (!document.body.contains(alertElement)) {
                return;
            }
            if (window.bootstrap) {
                window.bootstrap.Alert.getOrCreateInstance(alertElement)
                    .close();
            } else {
                alertElement.remove();
            }
        }, delay);
    };

    const showMessage = (text, level = "success") => {
        if (!messageContainer || !text) {
            return;
        }
        const alertElement = document.createElement("div");
        alertElement.className =
            `alert alert-${level} alert-dismissible fade show`;
        alertElement.setAttribute("role", "alert");
        alertElement.dataset.autoDismiss = "6000";

        const content = document.createElement("span");
        content.textContent = text;

        const closeButton = document.createElement("button");
        closeButton.type = "button";
        closeButton.className = "btn-close";
        closeButton.dataset.bsDismiss = "alert";
        closeButton.setAttribute("aria-label", "Dismiss message");

        alertElement.append(content, closeButton);
        messageContainer.append(alertElement);
        scheduleDismiss(alertElement);
    };

    document.querySelectorAll(".alert[data-auto-dismiss]")
        .forEach(scheduleDismiss);

    /* ------------------------------------------------------------------
       Shared helpers
       ------------------------------------------------------------------ */
    const postForm = async (form) => {
        const response = await fetch(form.action, {
            method: "POST",
            body: new FormData(form),
            headers: AJAX_HEADERS,
            credentials: "same-origin",
        });
        const isJson = (response.headers.get("content-type") || "")
            .includes("application/json");
        if (!isJson) {
            throw new Error("Unexpected response from the server.");
        }
        return response.json();
    };

    const setBusy = (form, busy) => {
        form.querySelectorAll("button[type=submit]").forEach((button) => {
            button.classList.toggle("is-busy", busy);
            button.setAttribute("aria-busy", String(busy));
        });
    };

    const setText = (selector, value) => {
        if (value === undefined) {
            return;
        }
        document.querySelectorAll(selector).forEach((element) => {
            element.textContent = value;
        });
    };

    const updateCartSummary = (data) => {
        const counter = document.getElementById("cart-count-number");
        const badge = document.getElementById("cart-count");
        if (counter && data.cart_count !== undefined) {
            counter.textContent = data.cart_count;
            if (badge) {
                badge.classList.remove("bump");
                // Reading offsetWidth restarts the CSS animation.
                void badge.offsetWidth;
                badge.classList.add("bump");
            }
        }
        setText("[data-cart-subtotal]", data.subtotal);
        setText("[data-cart-delivery]", data.delivery);
        setText("[data-cart-total]", data.total);
        setText("[data-cart-gap]", data.free_delivery_gap);
        if (data.qualifies_for_free_delivery !== undefined) {
            document.querySelectorAll("[data-cart-gap-note]")
                .forEach((note) => {
                    note.hidden = data.qualifies_for_free_delivery;
                });
        }
    };

    /**
     * Send a form with fetch and report the result. If anything unexpected
     * happens, fall back to a normal form submission so the action is
     * never silently lost.
     */
    const submitWithFetch = async (form, onSuccess) => {
        if (form.dataset.busy === "true") {
            // A request for this form is already on its way.
            return;
        }
        form.dataset.busy = "true";
        setBusy(form, true);
        try {
            const data = await postForm(form);
            updateCartSummary(data);
            showMessage(data.message, data.level || "info");
            if (data.ok && onSuccess) {
                onSuccess(data);
            }
        } catch (error) {
            form.dataset.noAjax = "true";
            form.submit();
        } finally {
            form.dataset.busy = "false";
            setBusy(form, false);
        }
    };

    /* ------------------------------------------------------------------
       2. Confirmation modal (falls back to window.confirm)
       ------------------------------------------------------------------ */
    const modalElement = document.getElementById("confirm-modal");
    const modalText = document.getElementById("confirm-modal-text");
    const modalAccept = document.getElementById("confirm-modal-accept");
    let pendingAction = null;

    const askToConfirm = (question, action) => {
        if (!modalElement || !window.bootstrap) {
            if (window.confirm(question)) {
                action();
            }
            return;
        }
        modalText.textContent = question;
        pendingAction = action;
        window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
    };

    if (modalAccept) {
        modalAccept.addEventListener("click", () => {
            const action = pendingAction;
            pendingAction = null;
            window.bootstrap.Modal.getOrCreateInstance(modalElement).hide();
            if (action) {
                action();
            }
        });
    }
    if (modalElement) {
        modalElement.addEventListener("hidden.bs.modal", () => {
            pendingAction = null;
        });
    }

    /* ------------------------------------------------------------------
       3 + 4. Cart and wishlist forms (one delegated submit listener)
       ------------------------------------------------------------------ */
    const removeCartLine = (form) => {
        const line = form.closest("[data-cart-line]");
        if (line) {
            line.remove();
        }
        if (!document.querySelector("[data-cart-line]")) {
            // Last item gone: reload to show the "cart is empty" state.
            window.location.reload();
        }
    };

    const handlers = {
        "js-cart-add": (form) => submitWithFetch(form),
        "js-cart-update": (form) => submitWithFetch(form, (data) => {
            const line = form.closest("[data-cart-line]");
            if (data.quantity === 0) {
                removeCartLine(form);
                return;
            }
            const input = form.querySelector("input[name=quantity]");
            if (input) {
                input.value = data.quantity;
            }
            const total = line && line.querySelector("[data-line-total]");
            if (total) {
                total.textContent = data.line_total;
            }
        }),
        "js-cart-remove": (form) => submitWithFetch(
            form, () => removeCartLine(form)
        ),
        "js-wishlist": (form) => submitWithFetch(form, (data) => {
            const button = form.querySelector("button[type=submit]");
            if (button) {
                button.textContent = data.saved
                    ? "Remove from wishlist"
                    : "Save to wishlist";
                button.setAttribute("aria-pressed", String(data.saved));
            }
        }),
    };

    const runHandler = (form) => {
        const name = Object.keys(handlers).find(
            (key) => form.classList.contains(key)
        );
        if (name) {
            handlers[name](form);
        } else {
            // A plain form that only needed confirming: send it normally.
            form.submit();
        }
    };

    document.addEventListener("submit", (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement) || form.dataset.noAjax) {
            return;
        }
        const isEnhanced = Object.keys(handlers).some(
            (key) => form.classList.contains(key)
        );
        const question = form.dataset.confirm;
        if (!isEnhanced && !question) {
            return;
        }
        if (isEnhanced && !form.checkValidity()) {
            // Let the browser show its own "please enter a number" hint.
            return;
        }
        event.preventDefault();
        if (question) {
            askToConfirm(question, () => runHandler(form));
        } else {
            runHandler(form);
        }
    });

    // Changing a quantity in the cart updates the totals straight away.
    document.querySelectorAll(".js-cart-update input[name=quantity]")
        .forEach((input) => {
            input.addEventListener("change", () => {
                if (input.form && input.form.reportValidity()) {
                    handlers["js-cart-update"](input.form);
                }
            });
        });

    /* ------------------------------------------------------------------
       5. Live search suggestions
       ------------------------------------------------------------------ */
    const searchInput = document.getElementById("site-search");
    const suggestionList = document.getElementById("search-suggestions");
    const suggestUrl = document.body.dataset.suggestUrl;

    const hideSuggestions = () => {
        if (suggestionList) {
            suggestionList.hidden = true;
            suggestionList.replaceChildren();
        }
    };

    const renderSuggestions = (results) => {
        suggestionList.replaceChildren();
        if (results.length === 0) {
            const empty = document.createElement("li");
            empty.className = "suggestion-empty";
            empty.textContent = "No matching products";
            suggestionList.append(empty);
        }
        results.forEach((result) => {
            const item = document.createElement("li");
            const link = document.createElement("a");
            link.href = result.url;
            const name = document.createElement("span");
            name.textContent = result.name;
            const meta = document.createElement("small");
            meta.textContent = `${result.category} - ${result.price}`;
            link.append(name, meta);
            item.append(link);
            suggestionList.append(item);
        });
        suggestionList.hidden = false;
    };

    if (searchInput && suggestionList && suggestUrl) {
        let timer = null;
        let latestRequest = 0;

        searchInput.addEventListener("input", () => {
            window.clearTimeout(timer);
            const term = searchInput.value.trim();
            if (term.length < 2) {
                hideSuggestions();
                return;
            }
            // Wait until typing pauses so we do not flood the server.
            timer = window.setTimeout(async () => {
                const requestId = ++latestRequest;
                try {
                    const url = `${suggestUrl}?q=${encodeURIComponent(term)}`;
                    const response = await fetch(url, {
                        headers: AJAX_HEADERS,
                    });
                    if (!response.ok) {
                        throw new Error("Search failed");
                    }
                    const data = await response.json();
                    // Ignore answers that arrive out of order.
                    if (requestId === latestRequest) {
                        renderSuggestions(data.results || []);
                    }
                } catch (error) {
                    hideSuggestions();
                }
            }, 250);
        });

        searchInput.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                hideSuggestions();
            }
        });

        document.addEventListener("click", (event) => {
            if (!event.target.closest(".site-search")) {
                hideSuggestions();
            }
        });
    }

    /* ------------------------------------------------------------------
       6. Product image zoom
       ------------------------------------------------------------------ */
    document.querySelectorAll("[data-zoom]").forEach((container) => {
        const image = container.querySelector("img");
        if (!image) {
            return;
        }
        const moveOrigin = (clientX, clientY) => {
            const box = container.getBoundingClientRect();
            const x = ((clientX - box.left) / box.width) * 100;
            const y = ((clientY - box.top) / box.height) * 100;
            image.style.transformOrigin = `${x}% ${y}%`;
        };
        const hoverCapable = window.matchMedia("(hover: hover)").matches;

        if (hoverCapable) {
            container.addEventListener("mouseenter", () => {
                container.classList.add("is-zoomed");
            });
            container.addEventListener("mousemove", (event) => {
                moveOrigin(event.clientX, event.clientY);
            });
            container.addEventListener("mouseleave", () => {
                container.classList.remove("is-zoomed");
            });
        } else {
            container.addEventListener("click", (event) => {
                moveOrigin(event.clientX, event.clientY);
                container.classList.toggle("is-zoomed");
            });
        }
        container.addEventListener("keydown", (event) => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                image.style.transformOrigin = "50% 50%";
                container.classList.toggle("is-zoomed");
            } else if (event.key === "Escape") {
                container.classList.remove("is-zoomed");
            }
        });
    });

    /* ------------------------------------------------------------------
       7. Image preview on the staff product form
       ------------------------------------------------------------------ */
    const preview = document.getElementById("image-preview");
    const imageInput = document.querySelector(
        "input[type=file][name=image]"
    );
    if (preview && imageInput) {
        const MAX_BYTES = 2 * 1024 * 1024;
        let objectUrl = null;

        imageInput.addEventListener("change", () => {
            if (objectUrl) {
                URL.revokeObjectURL(objectUrl);
                objectUrl = null;
            }
            const file = imageInput.files && imageInput.files[0];
            if (!file || !file.type.startsWith("image/")) {
                preview.hidden = true;
                return;
            }
            if (file.size > MAX_BYTES) {
                preview.hidden = true;
                imageInput.value = "";
                showMessage(
                    "That image is larger than 2 MB. Please choose a "
                    + "smaller file.",
                    "danger"
                );
                return;
            }
            objectUrl = URL.createObjectURL(file);
            preview.querySelector("img").src = objectUrl;
            preview.hidden = false;
        });
    }

    /* ------------------------------------------------------------------
       8. Small touches
       ------------------------------------------------------------------ */
    // Hints that only make sense when JavaScript is running.
    document.querySelectorAll(".js-show-with-script").forEach((element) => {
        element.hidden = false;
    });
    document.querySelectorAll(".js-hide-with-script").forEach((element) => {
        element.hidden = true;
    });

    // Sort / filter controls apply as soon as they change.
    document.querySelectorAll("form[data-auto-submit]").forEach((form) => {
        form.addEventListener("change", () => form.submit());
    });

    // Live "characters remaining" counter for the review box.
    const counter = document.getElementById("review-counter");
    if (counter) {
        const textarea = document.getElementById(counter.dataset.counterFor);
        if (textarea) {
            const limit = Number(textarea.getAttribute("maxlength")) || 1000;
            const update = () => {
                const left = limit - textarea.value.length;
                counter.textContent = `${left} characters remaining`;
            };
            textarea.addEventListener("input", update);
            update();
        }
    }
})();
