$('#comment').click(function(){
    $(this).animate({height: "120px"});
})

$('#dashboard-comments').click(function(){
    window.location.replace("/dashboard/comments");
})

$('#dashboard-add').click(function(){
    window.location.replace("/add");
});

$('#dashboard-posts').click(function(){
    window.location.replace("/dashboard/posts");
});

$('.nav-item').click(function(){
    window.location.replace($(this).attr('slug'));
});