#!/usr/bin/ruby -w
puts "Setting environment variables..."
ENV['FLASK_APP']="flaskr"
ENV['FLASK_ENV']="development"
puts "Starting up application..."
system(". venv/bin/activate")
system("flask run")
