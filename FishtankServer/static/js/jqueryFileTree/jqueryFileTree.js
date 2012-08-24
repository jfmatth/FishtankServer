// jQuery File Tree Plugin
//
// Version 1.01
//
// Cory S.N. LaViska
// A Beautiful Site (http://abeautifulsite.net/)
// 24 March 2008
//
// Visit http://abeautifulsite.net/notebook.php?article=58 for more information
//
// Usage: $('.fileTreeDemo').fileTree( options, callback )
//
// Options:  root           - root folder to display; default = /
//           script         - location of the serverside AJAX file to use; default = jqueryFileTree.php
//           folderEvent    - event to trigger expand/collapse; default = click
//           expandSpeed    - default = 500 (ms); use -1 for no animation
//           collapseSpeed  - default = 500 (ms); use -1 for no animation
//           expandEasing   - easing function to use on expand (optional)
//           collapseEasing - easing function to use on collapse (optional)
//           multiFolder    - whether or not to limit the browser to one subfolder at a time
//           loadMessage    - Message to display while initial tree loads (can be HTML)
//
// History:
//
// 1.01 - updated to work with foreign characters in directory/file names (12 April 2008)
// 1.00 - released (24 March 2008)
//
// TERMS OF USE
// 
// This plugin is dual-licensed under the GNU General Public License and the MIT License and
// is copyright 2008 A Beautiful Site, LLC. 
//


// Toggle the restore button for the checkout tree
function toggle_restore_button() {
	if ( $('#my_checkout').find('UL LI').length < 1 ) {
		$('#restore').hide();
		$('#restore_header').hide();
	} else {
		$('#restore').show();
		$('#restore_header').show();
	}
}


if(jQuery) (function($){

	$.extend($.fn, {
		fileTree: function(o, h) {
			// Defaults
			if( !o ) var o = {};
			if( o.root == undefined ) o.root = 'c:/';
			if( o.script == undefined ) o.script = 'jqueryFileTree.php';
			if( o.folderEvent == undefined ) o.folderEvent = 'click';
			if( o.expandSpeed == undefined ) o.expandSpeed= 500;
			if( o.collapseSpeed == undefined ) o.collapseSpeed= 500;
			if( o.expandEasing == undefined ) o.expandEasing = null;
			if( o.collapseEasing == undefined ) o.collapseEasing = null;
			if( o.multiFolder == undefined ) o.multiFolder = true;
			if( o.loadMessage == undefined ) o.loadMessage = 'Loading...';
			
			$(this).each( function() {
				function showTree(c, t, h) {
					$(c).addClass('wait');
					$(".jqueryFileTree.start").remove();
					$.post("/content/file_dir/", { dir: t, host: h }, function(data) {
						$(c).find('.start').html('');
						$(c).removeClass('wait').append(data);
						if( o.root == t ) $(c).find('UL:hidden').show(); else $(c).find('UL:hidden').slideDown({ duration: o.expandSpeed, easing: o.expandEasing });
						bindTree(c);
					});
				}
				
				function bindTree(t) {
					$(t).find('LI A').bind(o.folderEvent, function() {
						if( $(this).parent().hasClass('directory') ) {
							if( $(this).parent().hasClass('collapsed') ) {
								// Expand
								if( !o.multiFolder ) {
									$(this).parent().parent().find('UL').slideUp({ duration: o.collapseSpeed, easing: o.collapseEasing });
									$(this).parent().parent().find('LI.directory').removeClass('expanded').addClass('collapsed');
								}
								$(this).parent().find('UL').remove(); // cleanup
								
								
								
								showTree( $(this).parent(), escape($(this).attr('rel').match( /.*/ )), escape($(this).attr('class').match( /.*/ )) );
								$(this).parent().removeClass('collapsed').addClass('expanded');
							} else {
								// Collapse
								$(this).parent().find('UL').slideUp({ duration: o.collapseSpeed, easing: o.collapseEasing });
								$(this).parent().removeClass('expanded').addClass('collapsed');
							}
						} else {
							// this fires off when we click a file in the file tree
												
							var li_class = $(this).parent().attr('class')
							var a_class = $(this).attr('class')
							var a_rel = $(this).attr('rel')
							var a_id  = $(this).attr('id')
							
							// See if we've already added this file to the checkout tree.
							var exists = false;
							$('#my_checkout').find('LI A').each( function() {
							
									if ( $(this).attr('id').substring(1) == a_id ) {
										exists = true;
									} 
								}
							)
							
							// Add our new file in if it doesn't already exist in the checkout branch
							// prepend a "c" to the file id for the checked out file ids (it has to be unique within the document)
							if (exists == false) {		
								$('#my_checkout').find('UL').append('<li class="'+li_class+
																	'"><a href="#" class="'+a_class+'" rel="'+a_rel+'" id="c'+a_id+'">'+a_rel+'</a></li>');
								
								$('LI A#c'+a_id).bind(o.folderEvent, function() { 
									$(this).parent().remove();
									
									// Remove bold class from corresponding entry in file tree
									$('LI A#'+a_id).removeClass('restore');
									
									toggle_restore_button();
						
								} );
								
								$('LI A#'+a_id).addClass('restore'); // bold the entry in file tree
								
								toggle_restore_button();
							} else {
								$('LI A#c'+a_id).parent().remove();
								$('LI A#'+a_id).removeClass('restore'); // unbold the entry in filetree
								toggle_restore_button();
							}
							
						}
						return false;
					});
					// Prevent A from triggering the # on non-click events
					if( o.folderEvent.toLowerCase != 'click' ) $(t).find('LI A').bind('click', function() { return false; });
				}
				
				// bind our restore button.  this is triggered when restore is clicked to submit files.
				$('#restore').bind( 'click', function() {
							
					var files_to_restore = {};				
					var li_obj = $('#my_checkout').find('LI');
					
					
					// Get list of files
					li_obj.each( function() {
						host = $(this).find('A').attr('class');
						// file might be unnecessary now?
						//file = $(this).find('A').attr('rel');
						id = $(this).find('A').attr('id');
						
						if (!files_to_restore[host]) {
							files_to_restore[host] = Array();
						}
						
						files_to_restore[host].push(id);
						
					});
					
									
					$.post("/content/file_restore/", JSON.stringify({files: files_to_restore}), function(data) {
						alert("returned: " + data);
					});
				});
				
				
				// Loading message
				$(this).html('<ul class="jqueryFileTree start"><li class="wait">' + o.loadMessage + '<li></ul>');
				
				// For the checkout div
				$('#my_checkout').html('<ul class="jqueryFileTree"></ul>');
				
				// Hide our submit button and restore header until something is clicked
				$('#restore_header').hide();
				$('#restore').hide();
				
				// Get the initial file list
				showTree( $(this), "", "");
			});
		}
	});
	
})(jQuery);