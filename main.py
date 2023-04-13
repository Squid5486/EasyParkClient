import requests
import json
import time

defaultHeaders = {"easypark-application-channel-name" : "Android", 
                   "easypark-application-device-os" : "Android Mobile",
                   "easypark-application-version-number" : "16.5.0",
                   "easypark-application-build-number" : "1605001",
                   "easypark-application-device-os-version" : "29",
                   "easypark-application-market-country" : "SE",
                   "easypark-application-phone-number-country" : "SE",
                   "easypark-application-preferred-language" : "en-US",
                   "easypark-application-install-id" : "64b3b9a2-01cb-42bd-badd-e6aaae6b6f3b", # randomized every app install i believe
                   "Content-Type" : "application/json; charset=UTF-8",
                   "Host" : "app-bff.easyparksystem.net",
                   "Connection" : "Keep-Alive",
                   "Accept-Encoding" : "gzip",
                   "User-Agent" : "okhttp/4.9.3"}

baseUrl = "https://app-bff.easyparksystem.net"

secureInstallId = "0d2ac5e7-f6ae-4787-b10f-0d8e8819aefe" # this might also be randomized with every app install

def checkIfAccountExists(phoneNumber):
        url = baseUrl + "/android/api/account/exists"
        headers = defaultHeaders.copy()
        payload = '{"phoneNumber":"' + phoneNumber + '","canSplitTerms":true}'
        print(payload)
        r = requests.post(url, headers=headers, data=payload)
        print(r, r.text, r.headers)
        response = json.loads(r.text)
        if response["isKnownUser"]:
                return response["action"]

def requestVerificationCode(phoneNumber):
        print("Requesting verification code")
        url = baseUrl + "/android/api/account/requestVerificationCode"
        headers = defaultHeaders.copy()
        payload = '{"loginId": "","phoneNumber": "' + phoneNumber + '"}'
        r = requests.post(url, headers=headers, data=payload)
        print(r, r.text, r.headers)

def loginWithVerificationCode(phoneNumber, verifictionCode):
        url = baseUrl + "/android/api/account/loginWithVerificationCode"
        headers = defaultHeaders.copy()
        payload = '{"countryCode": "SE","phoneNumber": "' + phoneNumber + '","secureInstallId": "' + secureInstallId + '","verificationCode": "' + verifictionCode + '"}'
        r = requests.post(url, headers=headers, data=payload)
        print(r, r.text, r.headers)
        response = json.loads(r.text)

        options = {}

        for option in response["action"].split("?")[1].split("&"):
                options[option.split("=")[0]] = option.split("=")[1]

        # print(response["action"].split("?")[0], options["pendingAccessToken"])
        if response["action"].split("?")[0] == "easypark://app/multiFactorVerification":
                return response["action"].split("?")[0], options["pendingAccessToken"]
        elif response["action"] == "easypark://app/main?mimEnabled=true&findEnabled=true":
                credentials = {}
                credentials["idToken"] = response["sso"]["idToken"]
                credentials["parkingUserId"] = str(response["status"]["accounts"][0]["parkingUserId"])
                credentials["phoneNumber"] = phoneNumber
                if input("Save credentials to file? y/n ").lower() == "y":
                        writeCredsToFile(credentials)
                return response["action"], ""
        else:
                print("action not recognized", response["action"])
        

def verifyAccountWithLicensePlateNumber(phoneNumber, licensePlateNumber, pendingAccessToken): # not needed in all cases
        url = baseUrl + "/account/verifyAccountWithLicensePlateNumber"
        headers = defaultHeaders.copy()
        payload = '{"licensePlateNumber": "' + licensePlateNumber + '","pendingAccessToken": "' + pendingAccessToken + '","phoneNumber": "' + phoneNumber + '"}'
        r = requests.post(url, headers=headers, data=payload)
        print(r, r.text, r.headers)
        response = json.loads(r.text)
        credentials = {}
        credentials["idToken"] = response["sso"]["idToken"]
        credentials["parkingUserId"] = str(response["status"]["accounts"][0]["parkingUserId"])
        credentials["phoneNumber"] = phoneNumber
        if input("Save credentials to file? y/n ").lower() == "y":
                writeCredsToFile(credentials)
        return response["action"]

def loginToEasyPark():
        phoneNumber = input("Phone number written like +46000000000: ")
        action = checkIfAccountExists(phoneNumber)
        if action == "easypark://navigate/to/verification/code":
                requestVerificationCode(phoneNumber)
                verifictionCode = input("Verification code: ")
                action, pendingAccessToken = loginWithVerificationCode(phoneNumber, verifictionCode)
                if action == "easypark://app/multiFactorVerification":
                        licensePlateNumber = input("More verification needed. Enter a licensePlateNumber that has been used with your account: ").upper()
                        action = verifyAccountWithLicensePlateNumber(phoneNumber, licensePlateNumber, pendingAccessToken)
                        if action == "easypark://app/main?mimEnabled=true&findEnabled=true":
                                print("login succesful")
                elif action == "easypark://app/main?mimEnabled=true&findEnabled=true":
                        print("login successful")
                else:
                        print("action not recognized", action)
        else:
                print("action not recognized", action)
        
def parkingInformation(licensePlateNumber, parkingAreaNo):
        url = baseUrl + f"/android/api/parkingarea/SE/{parkingAreaNo}/parkinginformation"
        headers = defaultHeaders.copy()
        specificHeaders = {"X-Authorization" : "Bearer " + credentials["idToken"]}
        headers.update(specificHeaders)
        payload = '{"carCountryCode":"SE","carLicenseNumber":"' + licensePlateNumber + '","endDate":' + str(round((time.time() - 0.5) + 7200) * 1000) + ',"parkingAreaCountryCode":"SE","parkingAreaNo":' + parkingAreaNo + ',"parkingType":"NORMAL_TIME","parkingUserId":' + credentials["parkingUserId"] + ',"startDate":"' + str(round(time.time() - 0.5) * 1000) + '"}'
        r = requests.post(url, headers=headers, data=payload)
        print(r, r.text, r.headers)

def checkPrice(parkingAreaNo, licensePlateNumber): # experimental
        url = baseUrl + "/android/api/parking/price?includePriceInUserCurrency=false"
        headers = defaultHeaders.copy()
        specificHeaders = {"X-Authorization" : "Bearer " + credentials["idToken"]}
        headers.update(specificHeaders)
        payload = '{"carCountryCode": "SE","carLicenseNumber": "' + licensePlateNumber + '","endDate": 1681327320000,"parkingAreaCountryCode": "SE","parkingAreaNo": ' + parkingAreaNo + ',"parkingType": "NORMAL_TIME","parkingUserId": ' + credentials["parkingUserId"] + '}'
        r = requests.post(url, headers=headers, data=payload)

def parkingStart(licensePlateNumber, endDate, parkingAreaNo):
        url = baseUrl + "/android/api/parking/start?isAutomotive=false"
        headers = defaultHeaders.copy()
        specificHeaders = {"X-Authorization" : "Bearer " + credentials["idToken"]}
        headers.update(specificHeaders)
        payload = '{"carCountryCode":"SE","carLicenseNumber":"' + licensePlateNumber + '","endDate":' + endDate + ',"insufficientBalanceAllowed":false,"parkingAreaCountryCode":"SE","parkingAreaNo":' + parkingAreaNo + ',"parkingType":"NORMAL_TIME","parkingUserId":' + credentials["parkingUserId"] + ',"pointerLatitude":"59.63769077454013","pointerLongitude":"16.58932328340299"}'
        r = requests.post(url, headers=headers, data=payload)
        print(r, r.text, r.headers)
        response = json.loads(r.text)
        return response["id"]

def parkingStop(parkingId):
        url = baseUrl + f"/android/api/parking/{str(parkingId)}/stop?isAutomotive=false" # this needs some work. i dont know how to get parkingId if it isnt known since before
        headers = defaultHeaders.copy()
        specificHeaders = {"X-Authorization" : "Bearer " + credentials["idToken"]}
        headers.update(specificHeaders)
        r = requests.post(url, headers=headers) # no payload is needed
        print(r, r.text, r.headers)

def carsStatus(): # experimental
        url = baseUrl + "/android/api/account/cars"
        headers = defaultHeaders.copy()
        specificHeaders = {"X-Authorization" : "Bearer " + credentials["idToken"], "Cookie" : "token=" + credentials["idToken"]}
        headers.update(specificHeaders)
        r = requests.get(url, headers=headers) # no payload is needed
        print(r, r.text, r.headers)

def writeCredsToFile(credentials):
        with open('credentials.txt', 'w') as file:
                file.write(json.dumps(credentials))

def readCredentials():
        with open('credentials.txt') as file:
                return json.load(file)

def main():
        if fileFound:
                licensePlateNumber = input("licensePlateNumber: ").upper()
                parkingInformation(licensePlateNumber, parkingAreaNo)
                endDate = str(round((time.time() - 0.5) + 7200) * 1000) # park for 2 hours
                parkingId = parkingStart(licensePlateNumber, endDate, parkingAreaNo)
                print("parkingId = " + str(parkingId))
                # carsStatus()
        else:
                loginToEasyPark()

        # parkingInformation()
        # parkingStart()
        # parkingStop()

if __name__ == "__main__":
        credentials = {}
        print("EasyParkClient")
        parkingAreaNo = "62702"
        
        try: 
                credentials = readCredentials()
                print("credentials file found")
                fileFound = True
        except:
                print("credentials file not found")
                fileFound = False
        main()