// Get the board from the Server
function loadPositions () {
  const boardId = $('.container').attr('board_id');
  $.ajax({
    url: `${global.prot}://${global.domain}${global.apiPort}/api/v1/boards/${boardId}`,
    dataType: 'json',
    contentType: 'application/json',
    success: function (resp) {
      // change 'resp' for 'resp.nodes'
      // console.log(resp);
      for (const key in resp.nodes) {
        // console.log(key);
        $('[node_id="' + key + '"]').css('top', resp.nodes[key].y);
        $('[node_id="' + key + '"]').css('left', resp.nodes[key].x);
      }
      board = resp;
      drawConnections();
    }
  });
}
function goBack () {
  console.log('Go back', board);
  window.open('/user/' + board.user_id + '/boards', '_self');
}


let saving = false;

function getBoardView () {
  const boardId = $('.container').attr('board_id');
  $('.container').css('width', $('html').css('width'));
  // Detect when board name is pressed
  $('.board_name').on('click', function () {
    console.log('chage board name');
    $(this).css('display', 'none');
    $('[name=board_name]').css('display', 'block');
	$('[name=board_name]').css('background-color', 'white');
	// strip the boardname
    $('[name=board_name]').val($(this).text().replace(/^\s+|\s+$/g, ''));
  });
  $('[name=board_name]').focusout(function (evn) {
    // console.log($(this).val());
    if (saving === false) {
      $(this).css('display', 'none');
      $('.board_name').css('display', 'block');
      $('.board_name').text($(this).val());
      saving = true;
      saveBoardName($(this).val());
    }
  });
  $('[name=board_name]').on('keydown', function (evn) {
    console.log(evn.key);
    if (evn.key === 'Enter') {
      if (saving === false) {
        $(this).css('display', 'none');
        $('.board_name').css('display', 'block');
        $('.board_name').text($(this).val());
        saving = true;
        saveBoardName($(this).val());
      }
    }
  });
  let checkLite = window.location.href.indexOf('lite');
  let lite = '';
  if (checkLite !== -1) {
	  lite = '?lite=true';
  }
//   console.log('Lite', lite !== '');
  $.ajax({
    url: `${global.prot}://${global.domain}${global.apiPort}/api/v1/status`,
    success: function (data) {
      $.ajax({
		url: `${global.prot}://${global.domain}/boards/${boardId}/nodes${lite}`,
		contentType: 'application/json',
		dataType: 'json',
        success: async function (nodes) {
			// console.log('Lite', lite);
			if (lite !== '') {
				// console.log('Lite');
				setLiteView(nodes);
				setNodeSettings();
				setOpsListeners();
				setConnectionsListeners();
				$('#canvas_connections').attr('width', $('[grid="columns"]').css('width'));
				$('#canvas_connections').attr('height', $('.container').css('height'));
				$('#canvas_connections').css('width', $('[grid="columns"]').css('witdh'));
				$('#canvas_connections').css('height', $('.container').css('height'));
				drawConnections();
			} else {
				// console.log('No lite');
				unbindContainer();
				$('.container').append($(nodes.nodes));
				// await timeSleep(000);
				popup();
				setGrabbers();
				loadPositions();
				setNodeSettings();
				setOpsListeners();
				setConnectionsListeners();
				setMediaPlayerListeners();
				const width = window.outerWidth + 400;
				const height = window.outerHeight + 400;
				console.log(width, height);
				$('#canvas_connections').attr('width', width);
				$('#canvas_connections').attr('height', height + 1000);
				$('#canvas_connections').css('width', width);
				$('#canvas_connections').css('height', height + 1000);
				$('#canvas_grid').attr('width', width);
				$('#canvas_grid').attr('height', height + 1000);
				$('#canvas_grid').css('width', width);
				$('#canvas_grid').css('height', height + 1000);
				$('.container').css('width', width);
				$('.container').css('height', height);
				$('body').css('height', height);
				$('body').css('width', width);
				const gradient = 'linear-gradient(to right, var(--board_color), var(--board_color_end))';
				$('body').css('background-image', gradient);
				drawGrid();
				$('[action=user]').on('click', function () {
					goBack();
				});
				const nods = $('[cont_node_id]');
				console.log($(nods).length);
				if (nods.length === 1) {
					console.log('Show walkthrought');
					console.log($($(nods)[0]).position().left, $($(nods)[0]).position().top);
					oneNodeWalkthrought($($(nods)[0]).attr('cont_node_id'));
				}
			}
        }
      });
    },
    error: function (err) {
      console.log(err);
    }
  });
}
