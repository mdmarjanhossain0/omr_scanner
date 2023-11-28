# import the necessary packages
from imutils.perspective import four_point_transform
from imutils import contours
import numpy as np
import argparse
import imutils
import cv2
import random
import sys
import os
# user defined modules
import omr.worker.grader_util.grader_util as gu
import omr.worker.grader_util.grader_errors as ge
# from matplotlib import pyplot as plt

# construct the argument parser
# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--image", required=True,
#                 help="path to the input image")
# args = vars(ap.parse_args())

def omr_scanner(image_path):
    # Answer Key
    ques = [i for i in range(60)]
    opts = [1 for _ in range(60)]
    ANSWER_KEY = dict(zip(ques, opts))

    print(ANSWER_KEY)
    max_marks = 30
    positive_marking = 1
    negative_marking = 0
    bubble_thresh = 185

    def show_image(img, title="Original"):
        return
        cv2.imshow(title, img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    # load the image
    orig = cv2.imread(image_path)
    print(type(orig))
    print(orig.shape)
    image = orig.copy()
    # ratio = image.shape[0] / 800.0
    image = imutils.resize(image, height=1500)
    # gray it
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # blur it
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    # canny edge detection
    edged = cv2.Canny(gray, 20, 50)


    show_image(edged)

    # Find the contours
    cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)

    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    docCnts = None
    print(len(cnts))
    if len(cnts) > 0:
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        peri = cv2.arcLength(cnts[0], True)
        print(peri)
        approx = cv2.approxPolyDP(cnts[0], 0.02*peri, True)
        docCnts = approx
        # for c in cnts:
        #     print(type(c))
        #     print(c.shape)
        #     # print(c)
        #     # show_image(c)
        #     # calc the perimeter
        #     peri = cv2.arcLength(c, True)
        #     print(peri)
        #     approx = cv2.approxPolyDP(c, 0.02*peri, True)
        #     if len(approx) == 4:
        #         docCnts = approx
        #         break
    # try:
    #     docArea = cv2.contourArea(docCnts)
    #     print(docArea)
    #     if docArea <= 300000 or docArea >= 1000000:
    #         raise ge.PaperDetectionError(
    #             'Error in finding paper contour. Area of docCnts is {}'.format(docArea))
    # except ge.PaperDetectionError as e:
    #     sys.exit(e.message)

    # apply perspective transform to the shape
    paper = four_point_transform(image, docCnts.reshape(4, 2))
    warped = four_point_transform(gray, docCnts.reshape(4, 2))
    show_image(warped)
    # show_image(paper)
    # binarisation of image
    # instead of otsu thresholding
    # we have used adaptive thresholding

    thresh = cv2.adaptiveThreshold(
        warped, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    show_image(thresh)
    # thresh= cv2.medianBlur(thresh, 5)
    # show_image(thresh, "Filter thresh hold")
    # find contours in threshholded image
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,
                            cv2.CHAIN_APPROX_SIMPLE)

    # filter out contours with parents
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    # dc = cv2.drawContours(thresh, cnts, -1, (0,255,0), 3)
    # show_image(dc)
    print("number of contours of dc", len(cnts))
    # throw new error
    # try:
    #     if len(cnts) <= 240:
    #         raise ge.PaperContourError(
    #             'The contour of paper is not detected properly. May be only one external contour in the paper is detected.')
    # except ge.PaperContourError as e:
    #     sys.exit(e.message)

    # find question contours
    questions = gu.find_questions(cnts, paper)
    # We are now sorting from left to right by taking a batch of 16 contours
    # that are basically a whole row and then sorting them from increasing order of x

    questionCnts = gu.find_ques_cnts(questions)
    dc = cv2.drawContours(paper, questionCnts, -1, (0,255,0), 3)
    show_image(dc, "Paper dc")

    correct = 0
    wrong = 0
    # each question has 4 possible answers, to loop over the
    # question in batches of 4
    for (q, i) in enumerate(np.arange(0, len(questionCnts), 4)):
        try:
            # calculate the old question no
            old_question_no = gu.convert_ques_no(q, 15, 4)

            cnts = questionCnts[i:i+4]
            bubbled = [-1, -1]
            bubble_count = 0
            for (j, c) in enumerate(cnts):
                mask = np.zeros(thresh.shape, dtype='uint8')
                cv2.drawContours(mask, [c], -1, 255, -1)
                # apply the mask to the thresholded image, then
                # count the number of non-zero pixels in the
                # bubble area
                mask = cv2.bitwise_and(thresh, thresh, mask=mask)
                total = cv2.countNonZero(mask)

                # if total > current bubbled then
                # bubbled = total
                if bubbled[0] == -1 or bubbled[0] < total:
                    bubbled = (total, j)
                    if bubbled[0] > bubble_thresh:
                        bubble_count += 1
                else:
                    # update bubble thresh
                    # if total <= bubbled[0]
                    # this means that bubbled is not filled
                    # therefore we are updating bubble thresh to adjust to the pic
                    bubble_thresh = max(bubble_thresh, total+5)
                # print(old_question_no, bubble_thresh, total)
            # change the q to old q
            # as q0 -> 0
            # as q1 -> 15
            # as q2 -> 30 and so on
            color = (0, 0, 255)
            k = ANSWER_KEY[old_question_no]
            # check to see if the bubbled answer is correct
            if k == bubbled[1] and bubbled[0] > bubble_thresh:
                color = (0, 255, 0)
                correct += 1
            # wrongly attempted and negative marking
            elif k != bubbled[1] and bubbled[0] > bubble_thresh:
                wrong += 1

            if bubbled[0] > bubble_thresh:
                cv2.drawContours(paper, [cnts[k]], -1, color, 2)
        except:
            print("error")

    # grab the test taker
    score = (correct*positive_marking + wrong*negative_marking) / max_marks * 100
    info = {
        "correct": correct,
        "wrong": wrong,
        "score": score
    }
    return info
    print(info)
    # print("[INFO] correct: {}".format(correct))
    # print("[INFO] wrong: {}".format(wrong))
    # print("[INFO] score: {:.2f}%".format(score))
    cv2.putText(paper, "Correct: {}".format(correct), (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    cv2.putText(paper, "Wrong: {}".format(wrong), (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    cv2.putText(paper, "Score: {:.1f}%".format(score), (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    # comment it out in production
    show_image(image)
    show_image(paper)
    # use this in production
    image_name = args['image'].split('/')[-1]
    output_image = 'r/' + image_name
    # print('Saving Image to', output_image)
    directory = os.path.dirname(output_image)
    try:
        os.stat(directory)
    except:
        os.mkdir(directory)
    cv2.imwrite(output_image, paper)