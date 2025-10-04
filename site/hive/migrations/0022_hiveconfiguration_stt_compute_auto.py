from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("hive", "0021_hiveconfiguration_stt_model"),
    ]

    operations = [
        migrations.AlterField(
            model_name="hiveconfiguration",
            name="stt_compute",
            field=models.CharField(
                choices=[
                    ("auto", "Auto"),
                    ("int8", "int8 (CPU best)"),
                    ("int8_float16", "int8/FP16 (mixed)"),
                    ("float16", "float16 (GPU best)"),
                    ("float32", "float32"),
                ],
                default="auto",
                max_length=16,
            ),
        ),
    ]
