from django.shortcuts import render,redirect
from django.http import HttpResponse
from twilio.rest import Client
import smtplib
import numpy as np
from email.mime.text import MIMEText
from .models import AdminUser, Clinic, Disease, Patient, Consultation
from django.db.models import Q
from datetime import datetime, timedelta
import urllib.request
import urllib.parse

# Server IP Address.
serverIP = "127.0.0.1:8000"

# Create your views here.
# -------------------- Mail Code --------------------
def sendemail(subject,remail, message):
    sender_email = "healthalertxie@gmail.com"
    rec_email = remail
    password = "healthalert123"
    message = message
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = 'admin@example.com'
    msg['To'] = 'info@example.com'
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(sender_email, password)
    server.sendmail(sender_email,rec_email,msg.as_string())
    return(1)
# -------------------- SMS Code --------------------
def sendSMS(numbers, message):
    account_sid = 'AC0d37e654ec5d77d11ecce07755a51eca'
    auth_token = '4ab4224ca1c716156f8e8695d6eb4635'
    client = Client(account_sid, auth_token)

    client.messages.create(from_='+14343255160',body=message,to="+91"+numbers)
    return(1)

# -------------------- Login Code --------------------
def login(request):
    if 'id' in request.session:
        return redirect('/dashboard/')
    
    if request.method=='POST':
        email = request.POST.get("email","")
        password = request.POST.get("password","")
        
        data = AdminUser.objects.filter(Q(email=email) & Q(password=password))
        if data.count()==1:
            request.session['id'] = email
            request.session['type'] = 'admin'
            return redirect('/clinic/')
        else:
            data = Clinic.objects.filter(Q(email=email) & Q(password=password))
            if data.count()==1:
                request.session['id'] = email
                request.session['type'] = 'clinic'
                return redirect('/patients/')
            else:
                return render(request, "login.html", {"loginError":True,"logoutError":False})
    
    if 'msg' in request.session and request.session['msg'] == "logout":
        logoutError = True
        del request.session['msg']
    else:
        logoutError = False
    return render(request, "login.html", {"loginError":False,"logoutError":logoutError})
            
def logout(request):
    del request.session['id']
    del request.session['type']
    request.session['msg'] = 'logout'
    return redirect('/')

def dashboard(request):
    if 'id' not in request.session or 'type' not in request.session:
        return redirect('/')

    data = AdminUser.objects.raw("SELECT x.id, x.pincode,x.name,MAX(x.count) AS `maxCount`,(SELECT count(*) FROM `healthadmin_patient` WHERE `pincode`=x.pincode) AS `publicCount` FROM (SELECT c.id, d.name,p.pincode, count(p.id) as `count`, sum(p.id) as `sumcount` FROM `healthadmin_patient` p, `healthadmin_disease` d, `healthadmin_consultation` c WHERE c.patient = p.id AND c.disease = d.id AND c.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY p.pincode, d.name) AS x GROUP BY x.pincode")
    startDate = datetime.today() - timedelta(days=30)
    endDate = datetime.today()
    return render(request, "dashboard.html", {"data":data,"startDate":startDate,"endDate":endDate})

def diseaseInfo(request, disease):
    data = Disease.objects.filter(name=disease)
    number = Clinic.objects.raw("SELECT * from `healthadmin_clinic` ORDER BY `zipcode`")
    if data.count()==1:
        return render(request, "dinfo.html", {"data":data,"clinicnum":number})
    else:
        return HttpResponse("<h1>400</h1>Bad Request. Requested data does not exists")

def sendPincodeSMS(request,pincode,disease):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    global serverIP
    data = Patient.objects.raw("SELECT `id`,`name`,`mobile` FROM `healthadmin_patient` WHERE `pincode`=" + pincode)
    message = "Aapke area me " + disease + " ki bimari fail rahi hai. Krupiya apne parivaar ka khayal rkhe. Zyada info k liye visit kare http://" + serverIP + "/info/" + disease
    for x in data:
        pass
        #sendSMS(x.mobile, message)
    return redirect("/dashboard/")

def sendPincodeEmail(request,pincode,disease):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    global serverIP
    data = Patient.objects.raw("SELECT `id`,`email`,`name`,`mobile` FROM `healthadmin_patient` WHERE `pincode`=" + pincode)
    message = "Aapke area me " + disease + " ki bimari fail rahi hai. Krupiya apne parivaar ka khayal rkhe. Zyada info k liye visit kare http://" + serverIP + "/info/" + disease
    for x in data:
        pass
        subject="Disease Spreading in your Area"
        sendemail(subject,x.email,message)
    return redirect("/dashboard/")

def sendSMStoAll(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    global serverIP
    data = Patient.objects.raw("SELECT x.id, x.pincode,x.name,MAX(x.count) AS `maxCount` FROM (SELECT c.id, d.name,p.pincode, count(p.id) as `count` FROM `healthadmin_patient` p, `healthadmin_disease` d, `healthadmin_consultation` c WHERE c.patient = p.id AND c.disease = d.id AND c.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY p.pincode, d.name) AS x GROUP BY x.pincode")
    for x in data:
        data2 = Patient.objects.raw("SELECT `id`,`name`,`mobile`,`email`,`pincode`  FROM `healthadmin_patient` WHERE `pincode`=" + str(x.pincode))
        message = "Aapke area me " + x.name + " ki bimari fail rahi hai. Krupiya apne parivaar ka khayal rkhe. Zyada info k liye visit kare http://" + serverIP + "/info/" + x.name 
        for y in data2:
            pass
            #sendSMS(y.mobile, message)
    return redirect("/dashboard/")

def sendEmailtoAll(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    global serverIP
    data = Patient.objects.raw("SELECT x.id, x.pincode,x.name,MAX(x.count) AS `maxCount` FROM (SELECT c.id, d.name,p.pincode, count(p.id) as `count` FROM `healthadmin_patient` p, `healthadmin_disease` d, `healthadmin_consultation` c WHERE c.patient = p.id AND c.disease = d.id AND c.date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY) GROUP BY p.pincode, d.name) AS x GROUP BY x.pincode")
    for x in data:
        data2 = Patient.objects.raw("SELECT `id`,`name`,`mobile`,`email`,`pincode`  FROM `healthadmin_patient` WHERE `pincode`=" + str(x.pincode))
        message = "Aapke area me " + x.name + " ki bimari fail rahi hai. Krupiya apne parivaar ka khayal rkhe. Zyada info k liye visit kare http://" + serverIP + "/info/" + x.name 
        for y in data2:
            pass
            subject="Disease Spreading in your Area"
            sendemail(subject,y.email,message)
    return redirect("/dashboard/")

def changePassword(request):
    if 'id' not in request.session or 'type' not in request.session:
        return redirect('/')
    
    if request.method=="POST":
        oldPassword = request.POST.get("oldPassword","")
        newPassword = request.POST.get("newPassword","")

        data = AdminUser.objects.filter(Q(email=request.session['id']) & Q(password=oldPassword))
        if data.count()==1:
            for x in data:
                x.password = newPassword
                x.save()
                saveSuccess = "changed"
        else:
            saveSuccess = "incorrect"
    else:
        saveSuccess = False
    return render(request, "change-password.html", {"saveSuccess":saveSuccess})

# -------------------- Clinic Code --------------------
def clinic(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    global serverIP
    if request.method=="POST":
        name = request.POST.get("name","")
        doctorname = request.POST.get("doctorname","")
        doctorqualification = request.POST.get("doctorqualification","")
        address = request.POST.get("address","")
        zipcode = request.POST.get("zipcode","")
        phone = request.POST.get("phone","")
        email = request.POST.get("email","")
        password = request.POST.get("password","")
        data=" Health Alert | Clinic Resgistration\n Your Clinic is Succesfully registered \n Your Details:\n Clinic Name: "+name+"\n Doctor Name: "+doctorname+"\n Doctor Qualification: "+doctorqualification+"\n Clinic address: "+address+"\n Clinic Zipcode: "+zipcode+"\n Clinic Phone No.: "+phone+"\n Email: "+email+"\n Password: "+password+"\n Visit our website to login: http://"+serverIP+" \n Thank you|Team Health Alert...... "
        Clinic(name = name, doctorname = doctorname, doctorqualification = doctorqualification, address = address, zipcode = zipcode, phone = phone, email = email, password = password).save()
        saveSuccess = True
        subject="Clinic Registration"
        sendemail(subject,email,data)
    else:
        saveSuccess = False
    data = Clinic.objects.all()
    return render(request, "clinic.html", {"saveSuccess":saveSuccess,"data":data})

def editClinic(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    global serverIP
    if request.method=="POST":
        name = request.POST.get("name","")
        doctorname = request.POST.get("doctorname","")
        doctorqualification = request.POST.get("doctorqualification","")
        address = request.POST.get("address","")
        zipcode = request.POST.get("zipcode","")
        phone = request.POST.get("phone","")
        email = request.POST.get("email","")
        password = request.POST.get("password","")

        data = Clinic.objects.get(pk=id)
        data.name = name
        data.doctorname = doctorname
        data.doctorqualification = doctorqualification
        data.address = address
        data.zipcode = zipcode
        data.email = email
        data.phone = phone
        data.password = password
        data.save()
        message=" Health Alert | Clinic Updation\n Your Clinic data is Updated \n Your Details:\n Clinic Name: "+name+"\n Doctor Name: "+doctorname+"\n Doctor Qualification: "+doctorqualification+"\n Clinic address: "+address+"\n Clinic Zipcode: "+zipcode+"\n Clinic Phone No.: "+phone+"\n Email: "+email+"\n Password: "+password+"\n Visit our website to login: http://"+serverIP+" \n Thank you|Team Health Alert...... "
        subject="Clinic Updation"
        sendemail(subject,email,message)
        return redirect('/clinic/')
    
    data = Clinic.objects.filter(pk=id)
    return render(request, "edit-clinic.html", {"data":data})

def deleteClinic(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    data = Clinic.objects.filter(pk=id)
    data.delete()
    return redirect("/clinic/")

# -------------------- Disease Code --------------------
def disease(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    if request.method=="POST":
        name = request.POST.get("name","")
        cure = request.POST.get("cure","")
        precautions = request.POST.get("precautions","")
        symptoms = request.POST.get("symptoms","")

        Disease(name = name, cure = cure, precautions = precautions, symptoms = symptoms).save()
        saveSuccess = True
    else:
        saveSuccess = False
    
    data = Disease.objects.all()
    return render(request, "disease.html", {"saveSuccess":saveSuccess,"data":data})

def editDisease(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    if request.method=="POST":
        name = request.POST.get("name","")
        cure = request.POST.get("cure","")
        precautions = request.POST.get("precautions","")
        symptoms = request.POST.get("symptoms","")

        data = Disease.objects.get(pk=id)
        data.name = name
        data.cure = cure
        data.precautions = precautions
        data.symptoms = symptoms
        data.save()
        return redirect('/disease/')
    
    data = Disease.objects.filter(pk=id)
    return render(request, "edit-disease.html", {"data":data})

def deleteDisease(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    data = Disease.objects.filter(pk=id)
    data.delete()
    return redirect("/disease/")

# -------------------- Admin Code --------------------
def adminManager(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    global serverIP
    if request.method=="POST":
        name = request.POST.get("name","")
        email = request.POST.get("email","")
        password = request.POST.get("password","")

        AdminUser(name = name, email = email, password = password).save()
        saveSuccess = True

        message=" Health Alert | Admin Registration\n Your are Registers as Admin \n Your Details:\n Name: "+name+"\n Email: "+email+"\n Password: "+password+"\n Visit our website to login: http://"+serverIP+" \n Thank you|Team Health Alert...... "
        subject="Admin Registration"
        sendemail(subject,email,message)
    else:
        saveSuccess = False
    
    data = AdminUser.objects.all()
    return render(request, "admin.html", {"saveSuccess":saveSuccess,"data":data})

def editAdminManager(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    global serverIP
    if request.method=="POST":
        name = request.POST.get("name","")
        email = request.POST.get("email","")

        data = AdminUser.objects.get(pk=id)
        data.name = name
        data.email = email
        data.save()
        message=" Health Alert | Admin Updation\n Your data has been updated \n Your Details:\n Name: "+name+"\n Email: "+email+"\n Visit our website to login: http://"+serverIP+" \n Thank you|Team Health Alert...... "
        subject="Admin Updation"
        sendemail(subject,email,message)
        return redirect('/adminManager/')
    
    data = AdminUser.objects.filter(pk=id)
    return render(request, "edit-admin.html", {"data":data})

def deleteAdminManager(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='admin':
        return redirect('/')
    
    data = AdminUser.objects.filter(pk=id)
    data.delete()
    return redirect("/adminManager/")

# -------------------- Patients Code --------------------
def patients(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='clinic':
        return redirect('/')
    
    if request.method=="POST":
        name = request.POST.get("name","")
        mobile = request.POST.get("mobile","")
        address = request.POST.get("address","")
        email = request.POST.get("email","")
        pincode = request.POST.get("pincode","")

        Patient(name = name, mobile=mobile, address = address, email = email ,pincode = pincode, clinicID = request.session['id']).save()
        saveSuccess = True
    else:
        saveSuccess = False
    
    data = Patient.objects.filter(clinicID = request.session['id'])
    return render(request, "patients.html", {"saveSuccess":saveSuccess,"data":data})

def editPatients(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='clinic':
        return redirect('/')
    
    if request.method=="POST":
        name = request.POST.get("name","")
        mobile = request.POST.get("mobile","")
        address = request.POST.get("address","")
        email = request.POST.get("email","")
        pincode = request.POST.get("pincode","")

        data = Patient.objects.get(pk=id)
        data.name = name
        data.mobile = mobile
        data.address = address
        data.email = email
        data.pincode = pincode
        data.save()
        return redirect('/patients/')
    
    data = Patient.objects.filter(pk=id)
    return render(request, "edit-patients.html", {"data":data})

def deletePatients(request, id):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='clinic':
        return redirect('/')
    
    data = Patient.objects.filter(pk=id)
    data.delete()
    return redirect("/patients/")

# -------------------- Consultation Code --------------------
def consultation(request):
    if 'id' not in request.session or 'type' not in request.session or request.session['type']!='clinic':
        return redirect('/')
    
    if request.method=="POST":
        patient = request.POST.get("patient","")
        disease = request.POST.get("disease","")
        date = request.POST.get("date","")

        Consultation(patient = patient, disease=disease, date=date, clinicID = request.session['id']).save()
        saveSuccess = True
    else:
        saveSuccess = False
    
    data = Consultation.objects.raw("SELECT c.id,p.name as patient,p.mobile,p.pincode,d.name as disease FROM `healthAdmin_consultation` c, `healthAdmin_patient` p, `healthAdmin_disease` d WHERE c.patient = p.id AND c.disease = d.id AND c.clinicID = '" + request.session['id'] + "'")
    patients = Patient.objects.filter(clinicID = request.session['id'])
    diseases = Disease.objects.all()
    return render(request, "consultation.html", {"saveSuccess":saveSuccess,"data":data,"patients":patients,"diseases":diseases})

def editConsultation(request, id):
    if 'id' not in request.session or 'type' not in request.session  or request.session['type']!='clinic':
        return redirect('/')
    
    if request.method=="POST":
        patient = request.POST.get("patient","")
        disease = request.POST.get("disease","")
        date = request.POST.get("date","")
        
        data = Consultation.objects.get(pk=id)
        data.patient = patient
        data.disease = disease
        data.date = date
        data.save()
        return redirect('/consultation/')
    
    data = Consultation.objects.filter(pk=id)
    patients = Patient.objects.all()
    diseases = Disease.objects.all()
    return render(request, "edit-consultation.html", {"data":data,"patients":patients,"diseases":diseases})

def deleteConsultation(request, id):
    if 'id' not in request.session or 'type' not in request.session  or request.session['type']!='clinic':
        return redirect('/')
    
    data = Consultation.objects.filter(pk=id)
    data.delete()
    return redirect("/consultation/")

# -------------------- Patient Code --------------------
def appointment(request,a,id):
    if request.method=="POST":
        ids = request.POST.get("ids","")
        name = request.POST.get("name","")
        mobile = request.POST.get("phone","")
        pincode = request.POST.get("zipcode","")
        address = request.POST.get("address","")
        email = request.POST.get("email","")
        addDate = request.POST.get("date","")
        if request.POST.get("otp",""):
            o1=request.POST.get("otp","")
            o2=request.POST.get("otp2","")
            if o1==o2:
                data = Clinic.objects.raw("SELECT * FROM `healthadmin_clinic` WHERE `email`='"+ids+"'")
                Patient(name = name, mobile=mobile, address = address, email = email, pincode = int(pincode), addDate = addDate, clinicID = ids).save()
                for y in data:
                    pass
                    message=" Health Alert | Appointment Booked\n Hello "+name+" \n Your Appointment is sucessfully booked on:"+addDate+" \n Clinic Name:"+y.name+" \n Clinic Address:"+y.address+"\n Thank you|Team Health Alert...... "
                    #sendSMS(mobile, message)
                    subject="Appointment Booked"
                sendemail(subject,email,message)
            return redirect("/info/"+a+"/")

        otp=str(np.random.randint(100000,999999))
        message=" Health Alert | OTP Verification\n Hello "+name+" \n Your OTP Verfication Code is:"+otp+" \n Thank you/Team Health Alert...... "
        #sendSMS(mobile, message)
        subject="OTP Verification"
        sendemail(subject,email,message)
        return render(request, "otpvalid.html", {"id":ids,"name":name,"mobile":mobile,"pincode":pincode,"address":address,"email":email,"addDate":addDate, "otp":otp})
    data = Clinic.objects.raw("SELECT * FROM `healthadmin_clinic` WHERE `id`="+id+"")
    return render(request, "appointment.html", {"data":data})

def allclinic(request):
    number = Clinic.objects.raw("SELECT * from `healthadmin_clinic` ORDER BY `zipcode`")
    return render(request, "newappointment.html", {"clinicnum":number})
    
def paappointment(request,id):
    if request.method=="POST":
        ids = request.POST.get("ids","")
        name = request.POST.get("name","")
        mobile = request.POST.get("phone","")
        pincode = request.POST.get("zipcode","")
        address = request.POST.get("address","")
        email = request.POST.get("email","")
        addDate = request.POST.get("date","")
        if request.POST.get("otp",""):
            o1=request.POST.get("otp","")
            o2=request.POST.get("otp2","")
            if o1==o2:
                data = Clinic.objects.raw("SELECT * FROM `healthadmin_clinic` WHERE `email`='"+ids+"'")
                Patient(name = name, mobile=mobile, address = address, email = email, pincode = int(pincode), addDate = addDate, clinicID = ids).save()
                for y in data:
                    pass
                    message=" Health Alert | Appointment Booked\n Hello "+name+" \n Your Appointment is sucessfully booked on:"+addDate+" \n Clinic Name:"+y.name+" \n Clinic Address:"+y.address+"\n Thank you|Team Health Alert...... "
                    #sendSMS(mobile, message)
                    subject="Appointment Booked"
                sendemail(subject,email,message)
            return redirect("/appointment/")

        otp=str(np.random.randint(100000,999999))
        message=" Health Alert | OTP Verification\n Hello "+name+" \n Your OTP Verfication Code is:"+otp+" \n Thank you/Team Health Alert...... "
        #sendSMS(mobile, message)
        subject="OTP Verification"
        sendemail(subject,email,message)
        return render(request, "otpvalid.html", {"id":ids,"name":name,"mobile":mobile,"pincode":pincode,"address":address,"email":email,"addDate":addDate, "otp":otp})
    data = Clinic.objects.raw("SELECT * FROM `healthadmin_clinic` WHERE `id`="+id+"")
    return render(request, "appointment.html", {"data":data})

# -------------------- Forgot Password --------------------
def forgotpass(request):
    loginError=False
    if request.method=="POST":
        designation = request.POST.get("designation","")
        email = request.POST.get("email","")
        phone = request.POST.get("phone","")
        if request.POST.get("otp",""):
            o1=request.POST.get("otp","")
            o2=request.session['otp']
            if o1==o2:
                if designation=="clinic":
                    data = Clinic.objects.raw("SELECT * FROM `healthadmin_clinic` WHERE `email`='"+email+"' AND `phone`='"+phone+"'")
                elif designation=="admin":
                    data = AdminUser.objects.raw("SELECT * FROM `healthadmin_adminuser` WHERE `email`='"+email+"'")
                for y in data:
                    pass
                    message=" Health Alert | Forgot Password\n Hello "+y.name+" \n Designation: "+designation+" \n Username: "+y.email+" \n Password: "+y.password+" \n Thank you|Team Health Alert...... "
                    subject="Forgot Password"
                    sendemail(subject,email,message)
                    #sendSMS(mobile, message)
                    del request.session['otp']
                    return redirect("/")
        if designation=="clinic":
            data = Clinic.objects.filter(Q(email=email) & Q(phone=phone))
        elif designation=="admin":
            data = AdminUser.objects.filter(Q(email=email))
        if data.count()>=1:
            date = datetime.today()
            otp=str(np.random.randint(100000,999999))
            message=" Health Alert | OTP Verification \n Your OTP Verfication Code is:"+otp+" \n Thank you/Team Health Alert...... "
            subject="Forgot Password"
            sendemail(subject,email,message)
            #sendSMS(mobile, message)
            request.session['otp'] = otp
            return render(request, "otpforgot.html", {"designation":designation,"email":email,"phone":phone})
        else:
            loginError=True
            return render(request, "forgotpass.html", {"loginError":loginError})
    return render(request, "forgotpass.html", {"loginError":loginError})