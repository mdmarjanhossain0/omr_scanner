from django.shortcuts import render

from omr.worker.grader import omr_scanner

from omr.models import OMRExam, ScannedPaper









def home_view(request):
    context = {}
    if request.method == "POST":
        print(request.POST)
        print(request.FILES)
        omr = request.FILES.get("omr")
        print(omr)
        scanned_paper = ScannedPaper.objects.create(omr_sheet=omr)
        print(scanned_paper)
        print(scanned_paper.omr_sheet.path)
        answers = omr_scanner(scanned_paper.omr_sheet.path)
        print(answers)
        scanned_paper.correct = answers["correct"]
        scanned_paper.wrong = answers["wrong"]
        scanned_paper.save()
    omrs = ScannedPaper.objects.all().order_by("-pk")
    context["omrs"] = omrs


    return render(request, "home.html", context)


def controll_view(request):
    context = {}
    if request.method == "POST":
        print(request.POST)
        if request.POST.get("start", None):
            print("start")
            context["status"] = "started"
        else:
            print("stop")
            context["status"] = "stoped"

    return render(request, "controller.html", context)