import cv2
import numpy as np
import matplotlib.pyplot as plt
from math import ceil


def order_points(pts):
    pts = np.array(pts, dtype="float32")

    rect = np.zeros((4,2), dtype="float32")

    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]   # top-left
    rect[2] = pts[np.argmax(s)]   # bottom-right

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]  # top-right
    rect[3] = pts[np.argmax(diff)]  # bottom-left

    return rect.astype(int)



img = cv2.imread("arena3.pgm")

ori_image = img

plt.figure(figsize=(15, 10))
plt.subplot(1, 2, 1)
plt.imshow(img)

img[0:10, :] = (255, 255, 255)

img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

corners = cv2.goodFeaturesToTrack(
    img_gray,
    maxCorners=20,
    qualityLevel=0.1,
    minDistance=10,
    useHarrisDetector=True
)

corners = np.int0(corners)

rect = cv2.minAreaRect(np.array(corners))
box = cv2.boxPoints(rect)
box = np.intp(box)

box = order_points(box)

widthA = np.linalg.norm(box[2] - box[3])
widthB = np.linalg.norm(box[1] - box[0])
maxWidth = int(max(widthA, widthB))

heightA = np.linalg.norm(box[1] - box[2])
heightB = np.linalg.norm(box[0] - box[3])
maxHeight = int(max(heightA, heightB))

dst = np.array([
    [0, 0],
    [maxWidth - 1, 0],
    [maxWidth - 1, maxHeight - 1],
    [0, maxHeight - 1]
], dtype="float32")

M = cv2.getPerspectiveTransform(box.astype("float32"), dst)
warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

img = cv2.rotate(warped, cv2.ROTATE_180)





eyeball = 80


img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(img_gray, 253, 255, cv2.THRESH_BINARY)


contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
contours = list(contours)
length = len(contours)
i = 0
while i < length:
    if cv2.contourArea(contours[i]) > 20 or cv2.contourArea(contours[i]) == 0:
        contours.pop(i)
        length -= 1
        i -= 1
    i += 1



points = np.zeros((len(contours), 2))

i = 0
for contour in contours:
    points[i][0], points[i][1] = int(np.mean(contour[:, 0, 0])), int(np.mean(contour[:, 0, 1]))
    i += 1

points = points[np.lexsort((points[:, 0], points[:, 1]))]

x1 = 0
x2 = len(img[0])
y1 = 0
y2 = ceil((points[4][1]) + (eyeball / 42))

y_cropped = y2

img[y1:y2, x1:x2] = (0, 0, 0)

points_new = points[8 : ]
points_new = points_new[np.lexsort((points_new[:, 0], -points_new[:, 1]))]

x1 = ceil((points_new[0][0]) - (eyeball / 42))
x2 = len(img[0])
y1 = 0
y2 = len(img)

x_cropped = x1

img[y1:y2, x1:x2] = (0, 0, 0)
img[ceil(eyeball - (eyeball / 42)) : len(img), ceil((9 / 31) * len(img[0])) : len(img[0])] = (0, 0, 0)
img[0 : len(img), 0 : ceil(eyeball / 42)] = (0, 0, 0)

img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
kernel = np.ones((5,5), np.uint8)
thresh = cv2.dilate(thresh, kernel, iterations=1)


contours, _ = cv2.findContours(thresh[y_cropped : (eyeball - int(eyeball / 42)), int(eyeball / 42) : x_cropped], cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

img[y_cropped : y_cropped + 3, 2 : x_cropped] = (0, 0, 0)
img[y_cropped : ceil(eyeball - (eyeball / 42)), x_cropped - 3 : x_cropped] = (0, 0, 0)
img[y_cropped : len(img), ceil(eyeball / 42) : ceil(2.5 * (eyeball / 42))] = (0, 0, 0)
img[int(eyeball - 1.5 * (eyeball / 42)) : eyeball, ceil((9 / 31) * len(img[0])) : x_cropped] = (0, 0, 0)
img[int(eyeball - 1.5 * (eyeball / 42)) : len(img), ceil((9 / 31) * len(img[0]) - 1.5 * (eyeball / 42)) : ceil((9 / 31) * len(img[0]))] = (0, 0, 0)


for i in range(len(contours)):
    if 10 < cv2.contourArea(contours[i]) < 100:
        (x, y), _ = cv2.minEnclosingCircle(contours[i])
        cv2.circle(img[y_cropped : (eyeball - int(eyeball / 42)), int(eyeball / 42) : x_cropped], (int(x), int(y)), ceil(3 * (eyeball / 42)), (0, 0, 0), -1)
        cv2.circle(img[y_cropped : (eyeball - int(eyeball / 42)), int(eyeball / 42) : x_cropped], (int(x), int(y)), ceil(1.5 * (eyeball / 42)), (255, 255, 255), -1)
        
img = 255 - img


img[y1:y2, x1:x2] = (0, 0, 0)
img[ceil(eyeball - (eyeball / 42)) : len(img), ceil((9 / 31) * len(img[0])) : len(img[0])] = (0, 0, 0)
img[0 : len(img), 0 : ceil(eyeball / 42)] = (0, 0, 0)


points = points[np.lexsort((points[:, 0], points[:, 1]))]

x1 = 0
x2 = len(img[0])
y1 = 0
y2 = ceil((points[4][1]) + (eyeball / 42))

y_cropped = y2

img[y1:y2, x1:x2] = (0, 0, 0)

points_new = points[8 : ]
points_new = points_new[np.lexsort((points_new[:, 0], -points_new[:, 1]))]

x1 = ceil((points_new[0][0]) - (eyeball / 42))
x2 = len(img[0])
y1 = 0
y2 = len(img)

x_cropped = x1

Minv = np.linalg.inv(M)
img = cv2.rotate(img, cv2.ROTATE_180)
original = cv2.warpPerspective(img, Minv, (len(ori_image[0]), len(ori_image)))
img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

plt.subplot(1, 2, 2)
plt.imshow(original)
cv2.imwrite('arena_keepout.pgm', img) 
plt.show()