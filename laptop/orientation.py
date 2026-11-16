import tracker

def is_facing_forward(people: list[tracker.Person]):
    orientation = []
    for person in people:
        keypoints = person.keypoints
        nose = keypoints[0][2]
        left_eye = keypoints[1][2]
        right_eye = keypoints[2][2]

        if all(conf >= .7 for conf in (nose, left_eye, right_eye)):
            orientation.append((person, True))
        else:
            orientation.append((person, False))
    return orientation
