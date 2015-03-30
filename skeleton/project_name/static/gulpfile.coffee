gulp = require "gulp"
util = require "gulp-util"
filter = require "gulp-filter"
order = require "gulp-order"
concat = require "gulp-concat"
less = require "gulp-less"
batch = require "gulp-batch"
wrap = require "gulp-wrap"
sourcemaps = require "gulp-sourcemaps"
webserver = require "gulp-webserver"
source = require "vinyl-source-stream"
buffer = require "vinyl-buffer"
browserify = require "browserify"
watchify = require "watchify"
es = require "event-stream"
del = require "del"
minimist = require "minimist"
path = require "path"


# Load config
config = require "./config"


# Load command line parameters
knownOptions = 
  string: ['lib']


options = minimist(process.argv.slice(2), knownOptions)


_handleError = (err) ->
  util.log util.colors.red(err)
  util.beep()
  this.emit("end")


_getRelativePath = (full) ->
  # Get relative path to file
  path.relative(process.cwd(), full)


_eachFilename = (es, onFilename) ->
  es.map (file, cb) ->
    onFilename(_getRelativePath(file.path))
    cb(null, file)


_watch = false


_browserify = (cb, onBundle=null) ->

  numBundles = config.browserify.bundles.length
  config.browserify.bundles.forEach (bundleConfig) ->

    bundler = browserify(
      entries: bundleConfig.entries.map (entry) ->
        # Prepend ./ for browserify to work...
        './' + path.join(config.paths.src, entry)
      debug: _watch
      extensions: ['.coffee']
      paths: [
        path.join(options.lib, 'src/coffee'),
        path.join(process.cwd(), config.paths.src, 'bower_components')
      ]
    )

    bundle = ->
      src = bundler.bundle()
        .on("error", _handleError)
        .pipe source(bundleConfig.output)
        .pipe buffer()
      if onBundle
        src = onBundle(src)
      src = src.pipe gulp.dest('.', cwd: config.paths.build)
        .on "end", ->
          if numBundles
            numBundles--
            if numBundles == 0
              cb()

    rebundle = (paths) ->
      paths.forEach (path) ->
        util.log "Updated", util.colors.cyan(_getRelativePath(path))
      bundle()

    if _watch
      bundler = watchify(bundler)
      bundler.on("update", rebundle)

    bundler.transform("coffeeify")
    bundle()


gulp.task "browserify", ["clean"], (cb) ->
  _browserify(cb)


gulp.task "less", ["clean"], ->
  match = [
      path.join(config.paths.src, '**/*.less')
      path.join(options.lib, 'src/**/*.less')
  ]

  update = (update=false) ->
    src = gulp.src(config.less.sources, cwd: config.paths.src)
      .pipe less {
        paths: [
          path.join(options.lib, 'src/less'),
          path.join(process.cwd(), config.paths.src, 'bower_components')
        ]
      }
      .on("error", _handleError)
      .pipe gulp.dest('.', cwd: config.paths.build)

  gulp.watch match, (evt) ->
    util.log "Updated", util.colors.cyan(_getRelativePath(evt.path))
    update(true)

  update()


gulp.task "stylesheets", ["clean", "less"], ->
  match = [
      path.join(config.paths.src, '**/*.css')
      path.join(config.paths.build, '**/*.css')
  ]

  update = (update=false) ->
    entries = filter(config.stylesheets.entries)
    src = gulp.src(match)
      .pipe entries
      .pipe order(config.stylesheets.entries)
      .pipe _eachFilename es, (filename) ->
        if not update
          util.log "Using", util.colors.magenta(filename)
      .pipe concat(config.stylesheets.output)
      .pipe gulp.dest('.', cwd: config.paths.dist)
      .pipe _eachFilename es, (filename) ->
        if not update
          util.log "Combined as", util.colors.cyan(filename)
        else
          util.log "Recombined as", util.colors.cyan(filename)

  gulp.watch match, batch (events, cb)->
    update(true).on("end", cb)

  update()


gulp.task "javascripts", ["clean", "browserify"], ->
  match = [
    path.join(config.paths.src, '**/*.js')
    path.join(config.paths.build, '**/*.js')
  ]

  update = (update=false) ->
    entries = filter(config.javascripts.entries)
    src = gulp.src(match)
      .pipe entries
      .pipe order(config.javascripts.entries)
      .pipe _eachFilename es, (filename) ->
        if not update
          util.log "Using", util.colors.magenta(filename)
      # Make sure to load existing maps (like coffee sourcemaps)
      .pipe sourcemaps.init({loadMaps: true})
      # Wrap everything on one line, to preserve sourcemaps
      .pipe wrap('(function(){<%= contents %>})();')
      .pipe concat(config.javascripts.output)
      .pipe sourcemaps.write()
      .pipe gulp.dest('.', cwd: config.paths.dist)
      .pipe _eachFilename es, (filename) ->
        if not update
          util.log "Combined as", util.colors.cyan(filename)
        else
          util.log "Recombined as", util.colors.cyan(filename)

  gulp.watch match, batch (events, cb)->
    update(true).on("end", cb)

  update()


gulp.task "clean", (cb) ->
  del([
    path.join(config.paths.build, '**')
    path.join(config.paths.dist, '**')
  ], cb)


gulp.task "build", ["stylesheets", "javascripts"]


gulp.task "watch", ["configure_watch", "build"]


gulp.task "configure_watch", ->
  _watch = true


gulp.task "serve", ["watch"], ->
  util.log "Serving files from", util.colors.cyan(config.paths.dist)
  gulp.src(config.paths.dist)
    .pipe webserver {
      livereload: true,
      middleware: [
        (req, res, next) ->
          res.setHeader("Access-Control-Allow-Origin", "*")
          next()
      ]
    }