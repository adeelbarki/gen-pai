import torch
from torchvision import models, transforms
from PIL import Image

# Load pretrained DenseNet121 model
model = models.densenet121(pretrained=True)
model.classifier = torch.nn.Linear(1024, 2)
model.eval()

# Define image transform
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.Grayscale(num_output_channels=3),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225])
])

def predict(image: Image.Image) -> tuple[str, float]:
    image_tensor = transform(image).unsqueeze(0)
    with torch.no_grad():
        output = model(image_tensor)
        probs = torch.nn.functional.softmax(output, dim=1)
        _, pred = torch.max(probs, 1)

    label = ["Normal", "Pneumonia"][pred.item()]
    confidence = float(probs[0][pred])
    return label, round(confidence, 3)