#!/usr/bin/env python

from selenium import webdriver
from datetime import datetime
import sys, time, pickle
# from datetime import datetime as dt
from helper import *

amexWebsite = "https://online.americanexpress.com/myca/logon/us/action/LogonHandler?request_type=LogonHandler&Face=en_US&inav=iNavLnkLog"


def getAddedOffers(username, password, lastfive, nickname, outputlog = True, browser = "Chrome"):
  # re-route output
  orig_stdout = sys.stdout
  logfile = None
  if outputlog:
    # use current time as log file
    logfilename = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')
    logfilename = "offers " + logfilename.replace(':', '_') + ".csv"
    logfile = open('../tmp/' + logfilename, 'w+')
    sys.stdout = logfile
  donefilename = datetime.strftime(datetime.now(), '%Y-%m-%d')
  try:
    with open('../junk/'+donefilename+'.pickle', 'rb') as f:  # Python 3: open(..., 'rb')
      doneuser = pickle.load(f)
      # print(lastcards)
  except:
    doneuser = {"one": "two"}

  # input error handle
  if username == [] or password == [] or len(username) != len(password):
    print "username array does not have the same length as password array..."
    # close log file
    if outputlog:
      sys.stdout = orig_stdout
      logfile.close()
    return

  # use phantom JS / Firefox
  # driver = webdriver.PhantomJS()
  # driver = webdriver.Firefox()
  driver = getDriver(browser)
  majorOfferDollarMap = dict()
  majorOfferDescMap = dict()
  majorOfferDateMap = dict()
  majorDateOfferPair = set()
  userOffersList = []

  # loop through all username/password combinations
  for idx in range(len(username)):
    if username[idx] in doneuser:
      continue
    time.sleep(15)
    sys.stdout = orig_stdout
    sys.stdout.write('\r                                            \rRunning ' + username[idx])
    sys.stdout.flush()
    #print "\rRunning " + username[idx],
    if outputlog:
      sys.stdout = logfile

    eachbegintime = time.time()
    try:
      driver.get(amexWebsite)
    except:
      print "website is not available..."
      # close log file
      if outputlog:
        sys.stdout = orig_stdout
        logfile.close()
      return
    # fill and submit login form
    try:
      amexLogIn(driver, username[idx], password[idx])
#      print username[idx]
    except:
      print "username/password combination is incorrect..."
#      print username[idx]
      continue
    time.sleep(2)
#    closeFeedback(driver)
#    clickOnAddedToCard(driver)
#    closeFeedback(driver)
#    clickOnLoadMore(driver)
#    time.sleep(2)
#    closeFeedback(driver)

    # main program
    driver.get(added_page)
    offers = driver.find_elements_by_xpath('//*[@id="offers"]/div/section[2]/section/div')
    offers.pop(0)
    offerstext = [offer.text.encode('utf-8') for offer in offers]
    offersplit = [text.split('\n') for text in offerstext]
    offerDollarMap = dict()
    offerDescMap = dict()
    offerDateMap = dict()
    dateOfferPair = set()
    offersSet = set()
    # discard expired offers
    for sp in offersplit:
      if sp[2] == 'EXPIRES':
        expiration = sp[3]
      else:
        expiration = sp[2]
      offerDollarMap[sp[0]+sp[1]] = sp[0]
      offerDescMap[sp[0]+sp[1]] = sp[1]
      offerDateMap[sp[0]+sp[1]] = expiration
      dateOfferPair.add((expiration, sp[0]+sp[1]))
      offersSet.add(sp[0]+sp[1])
    majorOfferDollarMap.update(offerDollarMap)
    majorOfferDescMap.update(offerDescMap)
    majorOfferDateMap.update(offerDateMap)
    majorDateOfferPair.update(dateOfferPair)
    # accomadate new AMEX GUI
    if len(offers) == 0:
      offers = driver.find_elements_by_xpath("//*[contains(text(), 'Spend ') or contains(text(), 'Get ')]")
      offerstext = [n.text.encode('utf-8') for n in offers]
      offers = [offers[i] for i in range(len(offers)) if offerstext[i] != '']
      offerstext = filter(None, offerstext)
      offers = [e.find_element_by_xpath('..') for e in offers]
      offerstext = [n.text.encode('utf-8') for n in offers]
      offerstext = filter(None, offerstext)
      tmpnames = [n.split('\n')[1] for n in offerstext]
      offerDescMap = {n.split('\n')[1]: n.split('\n')[0] for n in offerstext}
      for n in tmpnames:
        offersSet.add(n)
      majorOfferDescMap.update(offerDescMap)
    userOffersList.append(offersSet)

    time.sleep(1)
    # logout
    try:
      amexLogOut(driver)
    except:
      pass
    doneuser[username[idx]] = password[idx]
    with open('../junk/'+donefilename+'.pickle', 'wb') as f:  # Python 3: open(..., 'rb')
      pickle.dump(doneuser, f)

    time.sleep(1)

  majorDateOfferList = list(majorDateOfferPair)
  majorDateOfferList.sort(key=lambda tup:tup[0])
  # write 1st line
  sys.stdout.write(',,')
  for dateOffer in majorDateOfferList:
    offer = majorOfferDollarMap[dateOffer[1]].replace(',', ' and')
    sys.stdout.write(','+offer)
  sys.stdout.write('\n,,')
  # write 2nd line
  for dateOffer in majorDateOfferList:
    desc = majorOfferDescMap[dateOffer[1]].replace(',', ' and')
    sys.stdout.write(','+desc)
  sys.stdout.write('\n,,')
  # write 3rd line
  for dateOffer in majorDateOfferList:
    date = majorOfferDateMap[dateOffer[1]]
    sys.stdout.write(','+date)
  sys.stdout.write('\n')
  # write the rest
  for i in range(len(username)):
    sys.stdout.write(username[i])
    sys.stdout.write("," + lastfive[i])
    sys.stdout.write("," + nickname[i])
    for dateOffer in majorDateOfferList:
      if dateOffer[1] in userOffersList[i]:
        sys.stdout.write(',+')
      else:
        sys.stdout.write(',')
    sys.stdout.write('\n')

  # close log file
  if outputlog:
    sys.stdout = orig_stdout
    logfile.close()

  # close browser
  driver.quit()


def main():
  try:
    username, password, lastfive, nickname = loadConfig2("../conf/config2.csv")
  except:
    username, password = loadConfig("../conf/config.csv")
    lastfive = []
    nickname = []
  getAddedOffers(username, password, lastfive, nickname, outputlog = True)

if __name__ == '__main__':
  main()


