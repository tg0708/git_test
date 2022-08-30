import sys

from flask_script import Manager
from app import create_app
# flask가  twisted 안에서 실행시키도록 해주는 라이브러리
from flask_twisted import Twisted
from twisted.python import log

if __name__ == "__main__":
  app = create_app()
  twisted = Twisted(app)
  log.startLogging(sys.stdout)
  
  app.logger.info(f"Running the app...")
  manager = Manager(app)
  manager.run()
  