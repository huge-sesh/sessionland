var scroll = function() {
	document.title = document.title.substr(1) + " " +document.title[0];
	setTimeout(scroll, 400);
}

var debug       = false;
var reverse     = false;
var startTime   = null;
var endTime     = null;
var backgrounds = null;
var last = function (list) { return list[list.length -1]; }
var log = function(str) { if (debug) console.log(str); }

var addPage = function (end) {
    page = $('<div class="page"></div>');
    page.css('background-image', 'url('+backgrounds[Math.floor(Math.random() * backgrounds.length)]['url']+')');
    page.posts = [];
    if (end) {
        $('#posts').append(page);
    } else {
        $('#posts').prepend(page);
    }
    log('add page: '+page.text());
    return page;
}

var pageSpace = function(page) {
    var remaining = page.width();
    page.find('.say').each(function (i, item) { 
        width = Math.max($(item).width(), 150);
        log($(item).find('.speech-bubble').html() + ': ' + width);
        remaining -= width;
    });
    log('remaining: ' + remaining);
    return remaining;
}

var addToPage = function(end, post) {
    if (reverse) end = !end;
    var page = end? $('div.page').last() : $('div.page').first();
    $('div.scratchbox').append(post.detach());
    if (pageSpace(page) < post.width()) page = addPage(end);
    if (end) { page.append(post.detach()); }
    else     { page.prepend(post.detach()); }
    var posts = page.find('.say');
    var space = Math.floor(pageSpace(page) / (posts.length * 2));
    log('space: '+space);
    page.find('.say').css('margin', '0 ' +space + 'px');
    return page;
}

var addPost = function (data, isThread) {
    if (endTime && startTime && data['dt'] < endTime && data['dt'] > startTime) return;
    log('addpost: '+data);
    var input = $('div#input').detach();
    var post = $('div#example-say').first().clone();
    post.find('.speech-bubble').html(data['content']);
    post.find('.avatar-img').attr('src', data['user']['avatar']);
    post.find('.avatar-link').attr('href', '/'+data['user']['id']);
    if (isThread) post.find('.speech-bubble').wrap($('<a href="/'+encodeURIComponent(data['content'])+'">'));
    post.removeAttr('id');
    var end = (!endTime || data['dt'] > endTime);
    if (!$('div.page').length) addPage(true);
    page = addToPage(end, post);
    if (end) {
        endTime = data['dt'];
        if (startTime == null) startTime = data['dt'];
    } else {
        startTime = data['dt'];
    }
    addToPage(true, input);
    return post;
}
var renderPosts = function (data) {
    if (!data || !data['posts']) return;
    $.each(data['posts'], function(i, item) {addPost(item, false)});
}

var renderThreads = function (data) {
    if (!data || !data['threads']) return;
    reverse = true;
    $.each(data['threads'], function(i, item) {addPost(item, true)});
}

$(function() {
    scroll();

    /* 
    * smartscroll: debounced scroll event for jQuery *
    * https://github.com/lukeshumard/smartscroll
    * Based on smartresize by @louis_remi: https://github.com/lrbabe/jquery.smartresize.js *
    * Copyright 2011 Louis-Remi & Luke Shumard * Licensed under the MIT license. *
    */

    var event = $.event,
        scrollTimeout;

    event.special.smartscroll = {
        setup: function () {
            $(this).bind("scroll", event.special.smartscroll.handler);
        },
        teardown: function () {
            $(this).unbind("scroll", event.special.smartscroll.handler);
        },
        handler: function (event, execAsap) {
            // Save the context
            var context = this,
              args = arguments;

            // set correct event type
            event.type = "smartscroll";

            if (scrollTimeout) { clearTimeout(scrollTimeout); }
            scrollTimeout = setTimeout(function () {
                $.event.handle.apply(context, args);
            }, execAsap === "execAsap" ? 0 : 100);
        }
    };

    $.fn.smartscroll = function (fn) {
        return fn ? this.bind("smartscroll", fn) : this.trigger("smartscroll", ["execAsap"]);
    };

    var thread = window.location.pathname;
    var loading = false;
    $(window).smartscroll(function (ev) {
        if ((window.scrollY == 0 || ($(document).height() - $(window).height() - scrollY == 0)) && !loading) {
            var params = window.scrollY == 0 ? {'comparator':'lt', 'dt':startTime} : {'comparator':'gt', 'dt':endTime}  
            loading = true;
            $.getJSON(thread+'.json',  params, function (json, textStatus, jqXHR) {
                log('got json');
                renderPosts(json);
            })
            .error(function(jqxhr, textStatus, errorThrown) {
                log('error: '+errorThrown+' '+textStatus)})
            .complete(function() {
                log('complete');
                loading = false;
                });
        }
    });
    var data = $.parseJSON($('div#data').html());
    backgrounds = data['page']
    addPage(true);
    addToPage(true, $('div#input').detach());
    renderPosts(data);
    renderThreads(data);

    var input = $('div#input');
    var hidden = input.find('div.user-input-hidden');
    input.buttons = false;
    input.find('textarea.user-input').bind('keyup', function() {
        var content = $(this).val().replace(/\n/g, '<br>');
        hidden.html(content);
        $(this).css('height', hidden.height());

        if (!input.buttons) {
            $.each(data['user']['avatar'], function(i, item) {
                button = $('<button name="avatar" type="submit" value="'+item['id']+'">'+item['name']+'</button>')
                    .hover(function() {
                        input.find('.avatar-img').attr('src', item['url']);});
                input.find('.avatar-buttons').append(button);
                input.buttons = true;
            });
        }
    });
});
