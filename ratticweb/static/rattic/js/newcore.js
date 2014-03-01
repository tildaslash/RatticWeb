var RATTIC = (function ($) {
    var my = {};
    my.api = {};
    my.controls = {};
    my.page = {};

    /********* Private Variables *********/
    var credCache = [];
    var rattic_meta_prefix = 'rattic_';
    var clip = new ZeroClipboard();

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
            url = my.page.getURLRoot() + 'api/v1/' + object + '/' + data + '/';
            data = undefined;
        } else {
            url = my.page.getURLRoot() + 'api/v1/' + object + '/';
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
            url = my.page.getURLRoot() + 'api/v1/' + object + '/' + data + '/';
            data = undefined;
        } else {
            url = my.page.getURLRoot() + 'api/v1/' + object + '/';
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
        target.trigger('getdata');
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

    function _performCredSearch() {
        searchstr = $(this).children('input[type=search]').val();

        if (searchstr.length > 0)
            window.location = my.page.getURLRoot() + "cred/list-by-search/" + searchstr + "/";

        return false;
    };

    function _checkAllClick() {
        me = $(this);
        targets = $(me.data('target'));
        mystatus = me.is(':checked');
        targets.each(function() {
            me = $(this);
            if (me.prop('checked') != mystatus)
                me.trigger('click');
        });
    };

    function _countChecks(checkboxes) {
        return checkboxes.filter(':checked').length;
    };

    function _enableButtonHandler() {
        $.each($(this).data('linked'), function() {
            button = $(this);
            target = $(button.data('target'));
            if (_countChecks(target) > 0) {
                button.removeClass('disabled');
            } else {
                button.addClass('disabled');
            }
        });
    };

    function _createGroupFormClear() {
        $("input#groupname").val('');
        $("button#saveGroupbutton").button('reset');
    };

    function _groupCreated(group) {
        $("select#id_group").append(
                '<option value="' + group['id'] + '">' +
                group['name'] +
                '</option>');

        $("select#id_group").val(group['id']);
    };

    function _createGroupClick() {
        ajax = my.api.createGroup(
                $("input#groupname").val(),
                function(){
                    $('#addGroup').modal('hide');
                    if (ajax.status == 201) _groupCreated(JSON.parse(ajax.responseText))
                },
                function(){
                    $('#addGroup').modal('hide');
                });

        return false;
    };

    function _setVisibility(item, state) {
        if (state == true) state = 'visible';
        if (state == false) state = 'hidden';
        $(item).css({visibility: state});
    };

    function _hideCopyButton() {
        me = $(this);
        hideTimeoutId = window.setTimeout(_hideCopyButtonTimer, 100);
        me.data('hideTimeoutId', hideTimeoutId)
    };

    function _hideCopyButtonTimer() {
        button = $($(me).data('copybutton'));
        _setVisibility(button, false);
        hideTimeoutId = -1;
    }

    function _showCopyButton() {
        hideTimeoutId = $(this).data('hideTimeoutId');
        if (hideTimeoutId != -1) {
            window.clearTimeout(hideTimeoutId);
            hideTimeoutId = -1;
        }
        button = $($(this).data('copybutton'));
        target = $(button.data('copyfrom'));
        target.trigger('getdatasync');
        _setVisibility(button, true);
        clip.glue(button);
    };

    function _copyButtonGetData(client) {
        me = $(this);
        target = $(me.data('copyfrom'));
        target.trigger('getdatasync');
        client.setText(target.text());
    };

    function _passfetcher() {
        me = $(this);
        cred_id = me.data('cred_id');
        my.api.getCred(cred_id, function(data) {
            me.text(data['password']);
        }, function(){});
    }

    function _passfetchersync() {
        me = $(this);
        cred_id = me.data('cred_id');
        me.text(my.api.getCredWait(cred_id)['password']);
    }

    /********* Public Variables *********/

    /********* Public Methods *********/
    /* Get Meta information */
    my.page.getMetaInfo = function(name) {
        return $('head meta[name=' + rattic_meta_prefix + name + ']').attr('content');
    }

    /* Gets the cred for the page from the head */
    my.page.getCredId = function() {
        return my.page.getMetaInfo('cred_id');
    }

    /* Gets the the url root from the page */
    my.page.getURLRoot = function() {
        return my.page.getMetaInfo('url_root');
    }

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

    /* Creates a password show and hide button */
    my.controls.searchForm = function(form) {
        form.on('submit', _performCredSearch);
    }

    /* Creates a checkbox that controls other checkboxes */
    my.controls.checkAll = function(checkboxes) {
        checkboxes.on('click', _checkAllClick);
    }

    /* A button that is enabled when at least one box is checked */
    my.controls.checkEnabledButton = function(buttons) {
        buttons.each(function() {
            button = $(this);
            target = $($(this).data('target'));
            if (typeof target.data('linked') == "undefined") {
                target.data('linked', []);
                target.on('click', _enableButtonHandler);
            }
            target.data('linked').push(button);
        });
    };

    /* Adds a 'New Group' button to the group select box for staff */
    my.controls.newGroupButton = function(selectboxes) {
        selectboxes.after('<a href="#addGroup" role="button" class="btn" data-toggle="modal" data-loading-text="Adding...">New</a>');

        $('#addGroup').on('show', _createGroupFormClear);
        $('#saveGroupButton').on('click', _createGroupClick);
    };

    /* Add copy buttons to table cells */
    my.controls.tableCopyButtons = function(cells) {
        if (!FlashDetect.installed) return false;

        cells.each(function() {
            // Get the players
            me = $(this);
            button = me.children('button');
            text = me.children('span');

            // Set data for callbacks
            button.data('copyfrom', text);
            button.data('copybutton', button);
            me.data('copybutton', button);
            text.data('copybutton', button);

            // Apply callbacks
            me.on('mouseleave', _hideCopyButton);
            text.on('mouseover', _showCopyButton);
            clip.on('mouseover', _showCopyButton);
            clip.on('dataRequested', _copyButtonGetData);
        });

        return true;
    };

    /* Add data fetchers for the password spans */
    my.controls.passwordFetcher = function(fetcher, id) {
        fetcher.data('cred_id', id);
        fetcher.on('getdata', _passfetcher);
        fetcher.on('getdatasync', _passfetchersync);
    };


    return my;
}(jQuery));

