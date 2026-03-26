import cv2
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

cnn = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
cnn = torch.nn.Sequential(*list(cnn.children())[:-1])
cnn = cnn.to(device)
cnn.eval()

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485,0.456,0.406],
        std=[0.229,0.224,0.225]
    )
])

def extract_video_features(video_path, num_frames=32):

    cap = cv2.VideoCapture(video_path)

    frames = []
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    step = max(total // num_frames, 1)

    for i in range(num_frames):

        cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)

        ret, frame = cap.read()

        if not ret:
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = Image.fromarray(frame)

        frame = transform(frame).unsqueeze(0).to(device)

        with torch.no_grad():

            feat = cnn(frame)

            feat = feat.view(-1)

        frames.append(feat.cpu())

    cap.release()

    features = torch.stack(frames)

    if features.shape[0] < num_frames:
        pad = torch.zeros(num_frames - features.shape[0], features.shape[1])
        features = torch.cat([features, pad])

    return features

def extract_features_from_frames(frames):

    features = []

    for frame in frames:

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        frame = Image.fromarray(frame)

        frame = transform(frame).unsqueeze(0).to(device)

        with torch.no_grad():

            feat = cnn(frame)

            feat = feat.view(-1)

        features.append(feat.cpu())

    features = torch.stack(features)

    return features