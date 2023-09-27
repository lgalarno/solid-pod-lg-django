$('.hide-show-ttl').hide();
$(function() {
    /////////////////////////////////////////////////////////////
    // hide-show ttl content
    /////////////////////////////////////////////////////////////
    // $('.hide-show-ttl').hide();
    $('.toggle-ttl').on('click',function() {
        console.log('click')
        $(this).text(function(_,currentText){
            return currentText == "▼" ? "▲" : "▼";
        });
        $('.hide-show-ttl').toggle();
    });
});
