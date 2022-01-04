// messages_widget functionality

// Reply Buttons:
// 1) add event listeners
// 2) fill out receiver and subject in modal

$('.btn.message-reply').click(function(){
    console.log('oi')
    var card = $($(this).attr("data-card"));

    var thread_id = $(card).attr("data-thread-id");
    var thread_title = $(card).find('h5#thread-subject').text();




    var modal = $('#message-reply-modal');
    $(modal).find("#message-reply-subject").text(thread_title);
    $(modal).find("input[name='thread']").value(thread_id);

    console.log(modal)
})
