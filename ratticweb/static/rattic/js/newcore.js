var RATTIC = (function ($) {
    var my = {};
    my.api = {};
    my.controls = {};
    my.page = {};

    /********* Private Variables *********/
    var credCache = [];

    /********* Private Methods **********/
    /* Gets a cookie from the browser. Only works for cookies that
     * are not set to httponly */
    function _getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    /* Shortcut to get the CSRF cookie from django. Tastypie needs this to
     * perform session based authentication. */
    function _getCsrf() {
        return _getCookie('csrftoken');
    }

    /* Generic API call to Rattic. Handles the CSRF token and callbacks */
    function _apicall(object, method, data, success, failure) {
        if (method == 'GET') {
            url = url_root + 'api/v1/' + object + '/' + data + '/';
            data = undefined;
        } else {
            url = url_root + 'api/v1/' + object + '/';
        }

        return $.ajax({
            url: url,
            type: method,
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', _getCsrf())
            },
            data: data,
            success: success,
            failure: failure,
        })
    }

    function _apicallwait(object, method, data) {
        if (method == 'GET') {
            url = url_root + 'api/v1/' + object + '/' + data + '/';
            data = undefined;
        } else {
            url = url_root + 'api/v1/' + object + '/';
        }

        return $.parseJSON($.ajax({
            url: url,
            type: method,
            contentType: 'application/json',
            beforeSend: function(jqXHR, settings) {
                jqXHR.setRequestHeader('X-CSRFToken', _getCsrf())
            },
            data: data,
            async: false,
        }).responseText);
    };

    function _passShowButtonClick() {
        target = $($(this).data('target'));
        switch ($(this).data('status')) {
            case 'hidden':
                _passShowButtonShow($(this), target);
                break;
            case 'shown':
                _passShowButtonHide($(this), target);
                break;
        };
        return false;
    };

    function _passShowButtonShow(button, target) {
        button.trigger('show');
        button.data('status', 'shown');
        button.html('<i class="icon-eye-close"></i');
        target.removeClass('passhidden');
        if (target.prop('tagName') == 'INPUT') {
            target.attr('type', 'text');
        }
    };

    function _passShowButtonHide(button, target) {
        button.trigger('hide');
        button.data('status', 'hidden');
        button.html('<i class="icon-eye-open"></i');
        target.addClass('passhidden');
        if (target.prop('tagName') == 'INPUT') {
            target.attr('type', 'password');
        }
    };


    /********* Public Variables *********/

    /********* Public Methods *********/
    /* Creates a Group */
    my.api.createGroup = function(name, success, failure) {
        var data = JSON.stringify({
            'name': name,
        });

        return _apicall('group', 'POST', data, success, failure);
    };

    /* Creates a Tag */
    my.api.createTag = function(name, success, failure) {
        var data = JSON.stringify({
            'name': name,
        });

        return _apicall('tag', 'POST', data, success, failure);
    };

    /* Gets the cred for the page from the head */
    my.page.getCredId = function() {
        return $('head meta[name=cred_id]').attr('content');
    }

    /* Gets a cred */
    my.api.getCred = function(id, success, failure) {
        if (typeof credCache[id] == 'undefined' ) {
            _apicall('cred',
                     'GET',
                     id,
                     function(data) {
                         credCache[id] = data;
                         success(data);
                     },
                     failure
                     );
        } else {
            success(credCache[id]);
        }
    };

    /* Gets a cred synchronous version */
    my.api.getCredWait = function(id) {
        if (typeof credCache[id] == 'undefined' ) {
            credCache[id] = _apicallwait('cred', 'GET', id);
            return credCache[id];
        } else {
            return credCache[id];
        }
    };

    /* Creates a password show and hide button */
    my.controls.passShowButton = function(buttons) {
        buttons.on('click', _passShowButtonClick);
        buttons.html('<i class="icon-eye-open"></i');
        buttons.data('status', 'hidden');
    }

    return my;
}(jQuery));

