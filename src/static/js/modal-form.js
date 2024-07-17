$(function() {
    /////////////////////////////////////////////////////////////
    //
    /////////////////////////////////////////////////////////////
    const modal_form = new bootstrap.Modal(document.getElementById("modal-form"))
    const modal_form_lg = new bootstrap.Modal(document.getElementById("modal-form-lg"))

    htmx.on("htmx:afterSwap", (e) => {
        // Response targeting #dialog => show the modal
        if (e.detail.target.id == "form-dialog") {
            modal_form.show()
        };
    });

    htmx.on("htmx:beforeSwap", (e) => {
        // Empty response targeting #dialog => hide the modal
        if (e.detail.target.id == "form-dialog" && !e.detail.xhr.response) {
            modal_form.hide()
            e.detail.shouldSwap = false
        }
    })
});
