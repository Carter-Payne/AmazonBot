from bs4 import BeautifulSoup as bs
import requests
from fake_useragent import UserAgent
import os, sys
from urllib.parse import urljoin
import mysql.connector
import time
import lxml
import cfscrape
import smtplib,ssl
from threading import Thread, Lock

class Data:

    def __init__(self,url=None,session=None,soop=None):
        self.session=session
        if soop is None:
            self.soup=Data.GetSoup(self,url)
        else: self.soup=soop
        self.price=Data.get_price(self)
        self.available=Data.Availability(self)
        self.name=Data.get_name(self)
        self.sale=Data.get_sale(self)[0]
        if self.sale is not None: self.sale=Data.percentintofloat(self)
        self.issale=Data.get_sale(self)[1]
        self.baseprice=Data.get_base_price(self)
        if self.baseprice is not None: self.baseprice=self.baseprice[1:]
        elif self.sale is not None: self.baseprice=float(self.price[1:])/((100.0-self.sale)/100)

    def Availability(self):
        '''#checks if the item is currently available'''
        try:
            text= (self.soup.select_one(('#availability > span:nth-child(4) > span'))).text.strip()
            if text=='Currently unavailable.':
                return False
            else: raise AttributeError
        except AttributeError:
            return True

    def percentintofloat(self):
        '''used to estimate base price if there is a sale percentage and sale price'''
        try:
            return float((self.sale[1:-1]))
        except ValueError:
            return float((self.sale[1:-2]))

    def get_base_price(self):
        '''checks multiple areas for the base price of an item'''
        try:
            text= self.soup.select_one('#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-small.aok-align-center > span > span.aok-relative > span > span > span.a-offscreen').text
            if text is not None and text!=" ": return text
            else: raise AttributeError
        except AttributeError:
            try:
                text= self.soup.select_one('#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center.aok-relative > span.aok-offscreen').text
                if text is not None and text!=" ": return text
                else: raise AttributeError
            except AttributeError:
                try:
                    text= self.soup.select_one('#corePrice_desktop > div > table > tbody > tr:nth-child(1) > td.a-span12.a-color-secondary.a-size-base > span.a-price.a-text-price.a-size-base > span.a-offscreen').text
                    if text is not None and text!=" ": return text
                    else: raise AttributeError     
                except AttributeError:           
                    return None

    def get_price(self):
        '''checks multiple different potential areas that amazon stores the price of an item in'''
        try:
            text = self.soup.select_one("#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center > span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay > span.a-offscreen").text
            if text is not None and text !=" ": return text
            else: raise AttributeError
        except AttributeError:
            try:
                text= self.soup.select_one("span.a-offscreen").text
                if text is not None and text !=" ": return text
                else: raise AttributeError
            except AttributeError:
                try:
                    text=self.soup.select_one("#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center > span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay > span:nth-child(2) > span.a-price-whole").text
                    if text is not None and text !=" ": return text
                    else: raise AttributeError
                except AttributeError:
                    try:
                        text.self.soup.select_one('#corePrice_feature_div > div > div > span.a-price.aok-align-center > span.a-offscreen').text
                        if text is not None and text !=" ": return text
                        else: raise AttributeError
                    except AttributeError:
                        try:
                            text=self.get_base_price()
                            if text is not None and text !=" ": return text
                            else: raise AttributeError
                        except AttributeError:
                            print("Product unable to be found.")
                            return None

    def get_sale(self):
        '''tries multiple potential locations for a sale percentage, returning none if none of them come up.'''
        try:
            return (self.soup.select_one("#corePriceDisplay_desktop_feature_div > div.a-section.a-spacing-none.aok-align-center > span.a-size-large.a-color-price.savingPriceOverride.aok-align-center.reinventPriceSavingsPercentageMargin.savingsPercentage").text,True)
        except AttributeError:
            try:
                text=(self.soup.select_one("td.a-span12.a-color-price.a-size-base>span.a-color-price")).text
                if text is not None: #text is not self contained, meaning I can't isolate the percentage without manually slicing the found string
                    if(text[len(text)-5] == " "):
                        text=text[len(text)-4:]
                    else:
                        text=text[len(text)-5:]
                    return (text,True)         
            except AttributeError:
                return (None,False)

    def GetSoup(self,url):
        '''obtains the soup associated with the url, first tries cfscrape, then response to access the data'''
        #headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        try:
            scraper = cfscrape.create_scraper()
            html_text = scraper.get(url).text
            soup = bs(html_text,'lxml')
            if (soup.get_name() is not None):
                return soup
            else: raise AttributeError
        except AttributeError or UnboundLocalError:       
            ua=UserAgent()
            hdr = {'User-Agent': ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept-Encoding': 'none',
                'Accept-Language': 'en-US,en;q=0.8',
                'Connection': 'keep-alive'}
            response = response.get(url,headers=hdr)
            soup = bs(response.content, 'lxml')
            return soup
        #print(soup)

    def GetSoups(soups,url,session,mutex=None):
        '''Same as the GetSoup function, but with multiple soups. Utilizes threading, so a mutex is implemented to prevent to many requests at once. Once again tries two different methods because amazon sucks'''
        ua=UserAgent()
        hdr = {'User-Agent': ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}
        #start_time=time.time()
        try:
            with mutex:
                time.sleep(1)
            scraper = cfscrape.create_scraper()
            html_text = scraper.get(url).text
            soup = bs(html_text,'lxml')
            if (soup is not None):
                soups.append((soup,url))
            else: raise AttributeError
        except AttributeError or UnboundLocalError:                           
            with mutex:
                time.sleep(1)#bypass bot detection
            response = session.get(url,headers=hdr)
            #print("--- %s seconds ---" % (time.time() - start_time))       
            soup = bs(response.content, 'lxml')
            soups.append((soup,url))
    
    def __str__(self=None,baseprice=None,name=None,sale=None,issale=None,price=None):
        if self:
            if self.issale:
                return (str(self.name)+" ($"+str(self.baseprice)+")"+ " is "+str(self.sale)+ "% off, selling for $"+self.price)
            else:
                return(str(self.name)+" is selling for $"+self.price)
        else:
            if issale:
                return (str(name)+" ($"+str(baseprice)+")"+ " is "+str(sale)+ "% off, selling for $"+price)
            else:
                return(str(name)+" is selling for $"+price)
        
    def get_name(self):
        try:
            return self.soup.find("span",attrs={'id':'productTitle'}).text.strip()
        except AttributeError:
            return None

class Account: 
    '''given the Username and password, creates an account that verifies that it is a real account and obtains the email associated with the account. Has a setting for bot to automate with BotRunner'''
    def __init__(self,Username=None,Password=None,bot=None):
        self.Username=Username
        self.Password=Password
        self.cnx=mysql.connector.connect(user='ENTER USERNAME', password='ENTER PASSWORD', host='ENTER HOST', database='ENTER DATABASE')
        self.mycursor=self.cnx.cursor(buffered=True)
        self.Mutex=Lock()
        self.session=requests.Session()
        if(bot is None or bot is False):
            if Account.login(self):
                self.Email=Account.Obtain_email(self)
            else:
                Account.close(self)
                print("Not a valid Username or Password")
                exit(-1)
    
    def Obtain_email(self):
        sql=('''SELECT EMAIL FROM UserInfo WHERE USERNAME='''+'\''+self.Username+'\'')
        self.mycursor.execute(sql)
        return str(self.mycursor.fetchall())[2:-3]
    
    def send_email(self,email):
        port = 465
        password = 'ENTER PASSWORD'
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL("smtp.gmail.com", port, context=context)
        server.login("ENTER EMAIL", password)
        sender_email = "ENTER EMAIL"
        receiver_email = email[1:-1]
        message = """Subject: Your Amazon Products:\n""".encode('UTF-8')
        sql='SELECT * FROM LINKS WHERE EMAIL=\'\''+email+'\'\''
        self.mycursor.execute(sql)
        for x in self.mycursor.fetchall():
            if x[7]=='Daily' or (x[7]=='OnSale' and x[3]==1) or (x[7]=='LowerToday' and x[6]==1):
                string=(Data.__str__(self=None,baseprice=x[2],issale=x[3],sale=x[4],price=x[5],name=x[8])+'\n\n')
                message+=(''.join(string).encode('UTF-8'))
        if(message != """Subject: Your Amazon Products:\n""".encode('UTF-8')):
            server.sendmail(sender_email, receiver_email, message)
            return("Email sent!")
        else:
            string='\n\nNo new deals to report :(\n\n'
            message+=(''.join(string).encode('UTF-8'))
            server.sendmail(sender_email, receiver_email, message)
            return("Email sent, but no items fit specifications.")

    def Commit(self):
        self.cnx.commit()
    
    def close(self):
        self.cnx.close()
    
    def login(self): 
        '''Checks if the given Username and password are associated with an account'''
        sql='''SELECT USERNAME, PASSWORD FROM UserInfo'''
        self.mycursor.execute(sql)
        for x in self.mycursor.fetchall():
            if(str(self.Username) in x and str(self.Password) in x):
                return(True)
        return(False)
            
    def has_links(self):
        '''checks if an email has any links associated with it'''
        sql='''SELECT URL FROM LINKS WHERE EMAIL= \'\''''+self.Email+"\'\'"
        self.mycursor.execute(sql)
        if self.mycursor.fetchall():
            return True
        return False
    
    def remove_link(self,link):
            '''removes a specified link from a user's email'''
            sql='''SELECT URL, EMAIL FROM LINKS'''
            self.mycursor.execute(sql)
            for x in self.mycursor.fetchall():
                if(str(link) in x and str(self.Email) in x):
                    sql='''DELETE FROM LINKS WHERE (URL, EMAIL)=(%s,%s)'''
                    val=(str(link),str(self.Email))
                    self.mycursor.execute(sql,val)
                    Account.Commit(self)
                    return("Link deleted")
            return("Link is not in database with associated email") 
    
    def add_link(self,link):
            sql='''SELECT URL, EMAIL FROM LINKS'''
            self.mycursor.execute(sql)
            for x in self.mycursor.fetchall():
                    if(str(link) in x and str(self.Email) in x):
                        return('Product already stored in database')
            if isValid(link,self.session):
                method=int(input('How would you like to be messaged about this product?\nType 1 for daily, 2 for whenever the item is on sale, and 3 for whenever the item\'s price was lower than the day before\nYour choice: '))
                match method:
                    case 1: method=str('Daily')
                    case 2: method=str('OnSale')
                    case 3: method=str('LowerToday')
                sql='INSERT INTO LINKS (URL, EMAIL, MESSAGEMETHOD) VALUES (%s, %s, %s)'
                val=(str(link),str(self.Email),str(method))
                self.mycursor.execute(sql,val)
                Account.Commit(self)
                Account.update_link(self,link)
                return('Product added')
            else:
                return('either not a valid Amazon link or link is not currently supported')

    
    def Lower_than_before(self,link,soup,email):
        '''Checks if the current value of the item is less than the value stored in the database. If so, it returns True'''
        sql='''SELECT SALEPRICE FROM LINKS WHERE URL=\''''+link+'\' AND EMAIL=\'\''''+email+'\'\''#MIGHT NOT WORK
        self.mycursor.execute(sql)
        if self.mycursor.fetchone() is not None:
            self.mycursor.execute(sql)            
            oldval=self.mycursor.fetchone()[0] 
            if oldval is not None and oldval=='Unavailable':sql='UPDATE LINKS SET LOWERTHANBEFORE = 1 WHERE URL=\''+link+'\'AND EMAIL=\'\''+email+'\'\''
            else:
                if(oldval is None or float(soup.price[1:])>=float(oldval)):
                    sql='UPDATE LINKS SET LOWERTHANBEFORE = 0 WHERE URL=\''+link+'\' AND EMAIL=\'\''+email+'\'\''
                else: 
                    sql='UPDATE LINKS SET LOWERTHANBEFORE = 1 WHERE URL=\''+link+'\'AND EMAIL=\'\''+email+'\'\''
        else: sql='UPDATE LINKS SET LOWERTHANBEFORE = 0 WHERE URL=\''+link+'\' AND EMAIL=\'\''+email+'\'\''
        self.mycursor.execute(sql)

    def update_link(self,url,soop=None,email=None): 
        '''creates a soup for the link and updates the product'''
        soup=Data(url,self.session,soop)
        if email is None: email=self.Email
        if soup.available is True:
            Account.Lower_than_before(self,url,soup, email)
            if soup.issale:#if there is a sale, the base price and sale price are different
                    sql='UPDATE LINKS SET BASEPRICE = \''+str(soup.baseprice)+'\', PERCENTAGE = \''+ str(soup.sale)+'\', ISSALE= 1, SALEPRICE = \''+str(soup.price[1:])+'\', NAME=\''+ str(soup.name)+'\' WHERE URL=\''+url+'\'AND EMAIL= \'\''+email+'\'\''
            else:#if there isn't a sale
                    sql='UPDATE LINKS SET BASEPRICE = \''+str(soup.price[1:])+'\', PERCENTAGE = \'0\', ISSALE= 0,  SALEPRICE = \''+str(soup.price[1:])+'\', NAME=\''+ str(soup.name)+'\' WHERE URL=\''+url+'\'AND EMAIL=\'\''+email+'\'\''
            self.mycursor.execute(sql)
        else:
            name='Unavailable'
            sql='UPDATE LINKS SET BASEPRICE = \''+str(name)+'\', PERCENTAGE = \'0\', ISSALE= 0,LOWERTHANBEFORE = 0, SALEPRICE = \''+str(name)+'\', NAME=\''+ str(soup.name)+'\' WHERE URL=\''+url+'\'AND EMAIL=\'\''''+email+'\'\''
            self.mycursor.execute(sql)
        Account.Commit(self)

    def update_all(self):
        sql=('''SELECT URL FROM LINKS''')
        self.mycursor.execute(sql)
        threads=[]
        soups=list()
        for x in self.mycursor.fetchall():
                y= Thread(target=Data.GetSoups, args=(soups,x[0],self.session,self.Mutex,))
                threads.append(y)
        for th in threads:
            th.start()       
        [th.join() for th in threads]
        sql=('''SELECT EMAIL FROM LINKS''')
        self.mycursor.execute(sql)
        emails=list()
        for x in self.mycursor.fetchall():
            emails.append(str(x[0])) 
        for x in range(len(soups)):
            Account.update_link(self=self,url=soups[x][1],soop=soups[x][0],email=emails[x])
        Account.send_emails(self)
    
    def send_emails(self):
        sql=('''SELECT DISTINCT EMAIL FROM LINKS''')
        self.mycursor.execute(sql)
        for x in self.mycursor.fetchall():
            Account.send_email(self,x[0])

    


    def delete_account(self):
        sql=('''DELETE FROM UserInfo WHERE USERNAME='''+'\''+self.Username+'\'')
        self.mycursor.execute(sql)
        if Account.has_links(self):
            sql=('''DELETE FROM LINKS WHERE EMAIL=\'\''''+self.Email+'\'\'')
            self.mycursor.execute(sql)
        Account.Commit(self)
        return("Account successfully deleted")
    
    def change_method(self,link):
        if isValid(link,self.session):
            method=int(input('How would you like to be messaged about this product?\nType 1 for daily, 2 for whenever the item is on sale, and 3 for whenever the item\'s price was lower than the day before\nYour choice: '))
            match method:
                case 1: method=str('Daily')
                case 2: method=str('OnSale')
                case 3: method=str('LowerToday')
            sql=('''UPDATE LINKS SET MESSAGEMETHOD ='''+'\''+method+'\''+' WHERE (URL=\''+link+'\' AND EMAIL=\'\''+self.Email+'\'\')')
            self.mycursor.execute(sql)
            Account.Commit(self)
            return("Method changed successfully")
        else:
            return("Not an Amazon link")
    
    
    def change_email(self,email):
        sql=('''UPDATE UserInfo SET EMAIL ='''+'\''+str(email)+'\''+' WHERE EMAIL='+self.Email)
        self.mycursor.execute(sql)
        Account.Commit(self)
        self.Email=str(email)
        return("Email Changed Successfully")
    
    def view_products(self):
        sql=('''SELECT NAME, URL FROM LINKS WHERE EMAIL=\'\''''+self.Email+'\'\'')
        self.mycursor.execute(sql)
        for x in self.mycursor.fetchall():
            print("\nItem name: "+x[0])
            print("URL= "+x[1])

def isValid(url,session):
        '''creates a connection and tests if the url has an amazon name associated with it. If so, it is valid and able to be put into the database.'''
        soup=Data(url,session)
        if soup.get_name() and soup.get_price():
            return True
        return False


def create_account(Username,password,email):
    '''creates an account to the mysql UserInfo database'''
    if Username and password and email:
        cnx = mysql.connector.connect(user='ENTER USERNAME', password='ENTER PASSWORD*', host='ENTER HOST', database='ENTER DATABASE')
        mycursor=cnx.cursor()
        sql='''SELECT USERNAME FROM UserInfo'''
        mycursor.execute(sql)
        if Username in str(mycursor.fetchall())[2:-3]:
            print("Your Username is not available")
            exit(-1)
        sql='''SELECT EMAIL FROM UserInfo'''
        mycursor.execute(sql)
        if email in str(mycursor.fetchall())[2:-3]:
            print("email already in use")
            exit(-1)
        sql='''INSERT INTO UserInfo (USERNAME, EMAIL, PASSWORD) VALUES (%s, %s, %s)'''
        val=(str(Username),str(email),str(password))
        mycursor.execute(sql,val)
        cnx.commit()
        cnx.close()
        return("Account Created!")
    else:
        print("You must enter a valid username, password, and email")
        exit(-1)

def Main():
    acct=int(input("Welcome to the Amazon Bot!\n\nIf you have an account, press 1\nIf you need to create an account, press 0\n\nYour Choice: "))

    if acct:
        Username=str(input('\nType your username: '))
        Password=str(input("\nType your password: "))
        Acct=Account(Username,Password)
        print("Successfully logged in\n")
    else:
        print("\nCreate your account:\n")
        a=input('Username = ')
        b=input('Password = ')
        c=input('Email = ')
        print("\n"+create_account(Username=a,password=b,email=c))
        print('\nRelaunch the application to login.')
        exit(-1)
    switch=0
    while(switch!=9):
        print("Press 1 to add an amazon link, 2 to remove an amazon link, 3 to change the frequency of emails, 4 to delete your account, 5 to view/change your email, 6 to view your products, 7 to update all of your products, 8 to send an email and 9 to exit the application")
        switch=int(input('\nYour Choice: '))
        match switch:
            case 1:
                url=input('\nEnter the Amazon url of the item you want to track\nYour URL: ')
                print(Acct.add_link(url)) 
            case 2:
                url=input('\nEnter the Amazon url of the item you want to remove\nYour URL: ')
                print(Acct.remove_link(url))   
            case 3:
                url=input('\nEnter the Amazon url of the item you want to change the message method of\nYour URL: ')
                print(Acct.change_method(url))
            case 4:
                check=int(input('Do you really want to delete your account? Type 1 if yes: '))
                if check:
                    print(Acct.delete_account())
                    exit(-1)
            case 5:
                check=int(input("Your email= "+Acct.Email+"\nWould you like to change your email?\nType 1 if yes: "))
                if check:
                    loop=False
                    while(loop is False):
                        newemail=input("\nEnter your new email: ")
                        loop=int(input("\nIs "+newemail+" the email you want to use?\nType 1 if yes: "))
                    print(Acct.change_email(newemail))
            case 6:
                Acct.view_products()
            case 7:
                start_time=time.time()                
                Acct.update_all()
                print("--- %s seconds ---" % (time.time() - start_time))      
            case 8:
                print(Acct.send_email(Acct.Email))
            case 9:
                Acct.close()
                exit(-1)

                



if __name__=="__main__":
    Main()
