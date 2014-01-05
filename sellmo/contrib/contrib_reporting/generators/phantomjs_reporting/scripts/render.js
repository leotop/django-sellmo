// Copyright (c) 2012, Adaptiv Design
// All rights reserved.
// 
// Redistribution and use in source and binary forms, with or without modification,
// are permitted provided that the following conditions are met:
//
//     * Redistributions of source code must retain the above copyright notice, this
// list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above copyright notice,
// this list of conditions and the following disclaimer in the documentation and/or
// other materials provided with the distribution.
//    * Neither the name of the <ORGANIZATION> nor the names of its contributors may
// be used to endorse or promote products derived from this software without specific
// prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
// IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
// INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
// NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
// PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
// WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.

var fs = require('fs');

// Wrap everything in one big try/catch,
// so we can call exit(1) on failure.
try {
    
    var system = require('system');
    var page = require('webpage').create();
    
    // Render callback
    page.onLoadFinished = function(status) {
        if (status == 'success') {
            // Render pdf to stdout
            page.render('/dev/stdout', { format: params.format });
            phantom.exit(0);
        }
        else {
            fs.write('/dev/stderr', "Page did not load correctly");
            phantom.exit(1);
        }
    };
    
    var params = {
        format : 'pdf'
    }
    
    // Collect arguments
    system.args.forEach(function (arg, i) {
        if (arg.indexOf('=') != -1)
        {
            params[arg.split('=')[0]] = arg.split('=')[1];
        }
    });
    
    // Confiure zoom
    if (params.zoom != undefined)
        page.zoomFactor = parseFloat(params.zoom);
    
    // Configure paper size
    paperSize = {}
        
    if (params.size != undefined)
        paperSize.format = params.size;
    if (params.orientation != undefined)
        paperSize.orientation = params.orientation;
    if (params.margin != undefined)
        paperSize.margin = params.margin;
        
    if (params.width != undefined)
        paperSize.width = params.width;
    if (params.height != undefined)
        paperSize.height = params.height;
    if (params.border != undefined)
        paperSize.border = params.border;
        
    page.paperSize = paperSize
    
    // Configure viewport
    if (params.viewport != undefined)
        page.viewportSize = {
            width : parseInt(params.viewport.split('x')[0]),
            height : parseInt(params.viewport.split('x')[1]),
        }
    
    // Read html from stdin, begin render
    page.content = fs.read('/dev/stdin');

} catch (err) {
    fs.write('/dev/stderr', err.toString());
    phantom.exit(1);
}