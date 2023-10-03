$(function() {
    /////////////////////////////////////////////////////////////
    //
    /////////////////////////////////////////////////////////////
    const modal_issuer = new bootstrap.Modal(document.getElementById("modal-issuer"))

    htmx.on("htmx:afterSwap", (e) => {
        // Response targeting #dialog => show the modal
        if (e.detail.target.id == "issuer-form-dialog") {
            modal_issuer.show()
        };
    });

    htmx.on("htmx:beforeSwap", (e) => {
        // Empty response targeting #dialog => hide the modal
        if (e.detail.target.id == "issuer-form-dialog" && !e.detail.xhr.response) {
            modal_issuer.hide()
            e.detail.shouldSwap = false
        }
    })
    // htmx.on("hidden.bs.modal", () => {
    //    modal_issuer.innerHTML = ""
    // })


    const modal_pod = new bootstrap.Modal(document.getElementById("modal-pod"))

        htmx.on("htmx:afterSwap", (e) => {
        // Response targeting #dialog => show the modal
        if (e.detail.target.id == "pod-form-dialog") {
            modal_pod.show()
        };
    });

    htmx.on("htmx:beforeSwap", (e) => {
        // Empty response targeting #dialog => hide the modal
        if (e.detail.target.id == "pod-form-dialog" && !e.detail.xhr.response) {
            modal_pod.hide()
            e.detail.shouldSwap = false
        }
    })

});
