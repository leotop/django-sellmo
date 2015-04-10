module.exports = 
  paths:
    src: './src/'
    build: './build/'
    dist: './dist/'
  browserify:
    bundles: [
      {entries: ['coffee/plugins/index.coffee'], output: 'plugins.js'}
    ]
  less:
    sources: ['less/screen.less']
  stylesheets: 
    entries: [
      'bower_components/select2/select2.css',
      'screen.css'
    ]
    output: 'shop/css/shop.css'
  javascripts:
    entries: [
      'bower_components/jquery/dist/jquery.js',
      'bower_components/bootstrap/js/tooltip.js',
      'bower_components/bootstrap/js/*.js',
      'bower_components/handlebars/handlebars.js',
      'bower_components/select2/select2.js',
      'plugins.js',
    ]
    output: 'shop/js/shop.js'
  collect:
    sources: [
      'bower_components/fontawesome/**/*.eot',
      'bower_components/fontawesome/**/*.svg',
      'bower_components/fontawesome/**/*.woff',
      'bower_components/fontawesome/**/*.woff2',
      'bower_components/bootstrap/dist/**/*.eot',
      'bower_components/bootstrap/dist/**/*.svg',
      'bower_components/bootstrap/dist/**/*.woff',
      'bower_components/bootstrap/dist/**/*.woff2',
    ]