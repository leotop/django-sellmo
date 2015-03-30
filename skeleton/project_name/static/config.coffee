module.exports = 
  paths:
    src: './src/'
    build: './build/'
    dist: './dist/'
  browserify:
    bundles: [
      {entries: ['coffee/app/index.coffee'], output: 'app.js'}
    ]
  less: 
    sources: ['less/screen.less']
  stylesheets: 
    entries: [
      'screen.css' 
    ]
    output: 'adaptmin/css/adaptmin.css'
  javascripts:
    entries: [
      'bower_components/jquery/dist/jquery.js',
      'bower_components/ember/ember-template-compiler.js',
      'bower_components/ember/ember.debug.js',
      'bower_components/ember-data/ember-data.prod.js',
      'ember-templates.js',
      'app.js',
    ]
    output: 'adaptmin/js/adaptmin.js'