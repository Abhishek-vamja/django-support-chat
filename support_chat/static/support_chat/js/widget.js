var SupportChat = (function () {
  var config = {};
  var state = {
    conv: null,
    ws: null,
    connected: false,
    visitor_name: null,
    visitor_email: null,
    rating: 0,
  };

  function init(opts) {
    config = opts || {};
    document.addEventListener('DOMContentLoaded', function () {
      bindUI();
    });
  }

  function bindUI() {
    var open = document.getElementById('support-chat-open');
    var panel = document.getElementById('support-chat-panel');
    var close = document.getElementById('sc-close');
    var prechat = document.getElementById('sc-prechat');
    var nameInput = document.getElementById('sc-name');
    var emailInput = document.getElementById('sc-email');
    var form = document.getElementById('sc-form');
    var input = document.getElementById('sc-input');
    var messages = document.getElementById('sc-messages');
    var endChatBtn = document.getElementById('sc-end-chat');
    var feedbackModal = document.getElementById('sc-feedback-modal');
    var modalClose = document.getElementById('sc-modal-close');
    var feedbackCancel = document.getElementById('sc-feedback-cancel');
    var feedbackSubmit = document.getElementById('sc-feedback-submit');
    var stars = document.querySelectorAll('.sc-star');

    // Initialize visibility: show pre-chat if no existing session
    toggleChat(!!state.conv);

    if (open) {
      open.addEventListener('click', function () {
        panel.setAttribute('aria-hidden', 'false');
        if (state.visitor_name || state.visitor_email) updateHeader();
        if (!state.conv && nameInput) nameInput.focus();
      });
    }
    
    if (close) {
      close.addEventListener('click', function () {
        panel.setAttribute('aria-hidden', 'true');
      });
    }

    if (prechat) {
      prechat.addEventListener('submit', function (e) {
        e.preventDefault();
        var name = nameInput && nameInput.value && nameInput.value.trim();
        var email = emailInput && emailInput.value && emailInput.value.trim();
        if (!name || !email) {
          appendSystem('Please provide both name and email to start.');
          if (!name && nameInput) nameInput.focus();
          else if (!email && emailInput) emailInput.focus();
          return;
        }
        startSession(name, email);
      });
    }

    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var text = input.value && input.value.trim();
        if (!text) return;
        input.value = '';
        input.focus();
        sendMessage(text);
      });
    }

    if (endChatBtn) {
      endChatBtn.addEventListener('click', function () {
        endChat();
      });
    }

    // Star rating
    stars.forEach(function (star) {
      star.addEventListener('click', function () {
        state.rating = parseInt(this.getAttribute('data-rating'), 10);
        stars.forEach(function (s) {
          if (parseInt(s.getAttribute('data-rating'), 10) <= state.rating) {
            s.classList.add('active');
          } else {
            s.classList.remove('active');
          }
        });
      });
    });

    if (modalClose) {
      modalClose.addEventListener('click', function () {
        closeFeedbackModal();
      });
    }

    if (feedbackCancel) {
      feedbackCancel.addEventListener('click', function () {
        closeFeedbackModal();
      });
    }

    if (feedbackSubmit) {
      feedbackSubmit.addEventListener('click', function () {
        submitFeedback();
      });
    }
  }

  function toggleChat(active) {
    try {
      var pre = document.getElementById('sc-prechat');
      var msg = document.getElementById('sc-messages');
      var f = document.getElementById('sc-form');
      var footer = document.getElementById('sc-footer');
      if (!pre || !msg || !f || !footer) return;
      if (active) {
        pre.setAttribute('aria-hidden', 'true');
        pre.style.display = 'none';
        msg.removeAttribute('aria-hidden');
        msg.style.display = '';
        f.removeAttribute('aria-hidden');
        f.style.display = '';
        footer.removeAttribute('aria-hidden');
        footer.style.display = '';
      } else {
        pre.removeAttribute('aria-hidden');
        pre.style.display = '';
        msg.setAttribute('aria-hidden', 'true');
        msg.style.display = 'none';
        f.setAttribute('aria-hidden', 'true');
        f.style.display = 'none';
        footer.setAttribute('aria-hidden', 'true');
        footer.style.display = 'none';
      }
    } catch (e) {}
  }

  function startSession(name, email) {
    if (!name || !email) return;
    fetch((config.api_root || '') + '/support_chat/api/create_session/', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({name: name, email: email})
    }).then(function (r) { return r.json(); })
      .then(function (data) {
        state.conv = data.conversation_id;
        state.visitor_name = name;
        state.visitor_email = email;
        updateHeader();
        toggleChat(true);
        appendSystem('Hi ' + name + '! 👋 How can we help you today?');
        var input = document.getElementById('sc-input');
        if (input) input.focus();
        connectWS();
      }).catch(function () { alert('Could not create session'); });
  }

  function endChat() {
    if (!state.conv) return;
    // Show feedback modal
    var modal = document.getElementById('sc-feedback-modal');
    if (modal) modal.style.display = 'flex';
  }

  function closeFeedbackModal() {
    var modal = document.getElementById('sc-feedback-modal');
    if (modal) modal.style.display = 'none';
    resetFeedback();
  }

  function submitFeedback() {
    var feedbackText = document.getElementById('sc-feedback-text');
    var feedback = feedbackText ? feedbackText.value.trim() : '';
    
    // Send feedback to server (optional)
    if (state.conv) {
      fetch((config.api_root || '') + '/support_chat/api/send_feedback/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          conversation_id: state.conv,
          rating: state.rating,
          feedback: feedback
        })
      }).catch(function () { console.log('Feedback submission failed'); });
    }

    closeFeedbackModal();
    closeChat();
  }

  function resetFeedback() {
    state.rating = 0;
    var feedbackText = document.getElementById('sc-feedback-text');
    if (feedbackText) feedbackText.value = '';
    document.querySelectorAll('.sc-star').forEach(function (star) {
      star.classList.remove('active');
    });
  }

  function closeChat() {
    state.conv = null;
    state.ws = null;
    state.connected = false;
    state.visitor_name = null;
    state.visitor_email = null;
    
    // Clear messages
    var messages = document.getElementById('sc-messages');
    if (messages) messages.innerHTML = '';
    
    // Clear inputs
    var nameInput = document.getElementById('sc-name');
    var emailInput = document.getElementById('sc-email');
    if (nameInput) nameInput.value = '';
    if (emailInput) emailInput.value = '';
    
    // Reset to pre-chat
    toggleChat(false);
    
    // Close panel
    var panel = document.getElementById('support-chat-panel');
    if (panel) panel.setAttribute('aria-hidden', 'true');
  }

  function wsOrigin() {
    if (config.ws_url) return config.ws_url.replace(/\/$/, '');
    var origin = window.location.origin;
    return origin.replace(/^http/, 'ws');
  }

  function connectWS() {
    if (!state.conv) return;
    var url = wsOrigin() + '/ws/support/conversation/' + state.conv + '/';
    try {
      state.ws = new WebSocket(url);
    } catch (err) {
      console.warn('WebSocket not available', err);
      state.ws = null;
      return;
    }

    state.ws.onopen = function () {
      state.connected = true;
      appendSystem('Connected to support team');
    };
    state.ws.onmessage = function (ev) {
      try {
        var data = JSON.parse(ev.data);
        if (data.type === 'message' && data.payload) {
          var p = data.payload;
          if (p.sender_type !== 'visitor') {
            appendMessage(p.sender_type || 'system', p.message);
          }
        } else if (data.type === 'message' && data.message) {
          if (data.message.sender_type !== 'visitor') {
            appendMessage(data.message.sender_type || 'system', data.message.message);
          }
        } else if (data.type === 'agent_assigned') {
          appendSystem('Agent ' + (data.agent_name || 'joined'));
        }
      } catch (e) {
        console.error('WS message error:', e);
      }
    };
    state.ws.onclose = function () {
      state.connected = false;
      appendSystem('Connection lost. Please try again.');
      state.ws = null;
    };
    state.ws.onerror = function () { /* ignore */ };
  }

  function sendMessage(text) {
    appendMessage('visitor', text);
    
    if (state.connected && state.ws) {
      var payload = JSON.stringify({type: 'message', sender_type: 'visitor', sender_id: null, message: text});
      state.ws.send(payload);
    } else {
      fetch((config.api_root || '') + '/support_chat/api/send_message/', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({conversation_id: state.conv, sender_type: 'visitor', sender_id: null, message: text})
      }).catch(function () { appendSystem('Failed to send message'); });
    }
  }

  function appendMessage(sender, text, self) {
    var box = document.getElementById('sc-messages');
    if (!box) return;
    var el = document.createElement('div');
    el.className = 'sc-message ' + (sender === 'visitor' ? 'visitor' : sender === 'agent' ? 'agent' : 'system');
    
    var content = document.createElement('div');
    content.className = 'sc-message-content';
    content.textContent = text;
    el.appendChild(content);
    
    box.appendChild(el);
    box.scrollTop = box.scrollHeight;
  }

  function appendSystem(text) {
    appendMessage('system', text);
  }

  function updateHeader() {
    try {
      var headerTitle = document.querySelector('.sc-header .sc-header-content .sc-title');
      var headerSub = document.querySelector('.sc-header .sc-header-content .sc-subtitle');
      if (headerTitle && state.visitor_name) headerTitle.textContent = state.visitor_name;
      if (headerSub && state.visitor_email) headerSub.textContent = state.visitor_email;
    } catch (e) {
      console.warn('Failed to update header', e);
    }
  }

  return {init: init};
})();

if (typeof window !== 'undefined') window.SupportChat = SupportChat;
