#from mypack.restpack import RestPack 

#if __name__ == "__main__":
#    RestPack().run(debug=True)
  ##This code imports the Flask app from the restpack module and runs it in debug mode.

from myrest.restpack import RestPack


if __name__ == "__main__":
    RestPack().run()

# This code imports the RestPack class from the restpack module and runs it in debug mode