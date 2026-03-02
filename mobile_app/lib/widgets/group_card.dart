import 'package:flutter/material.dart';
import '../config/theme/app_colors.dart';
import '../services/api_services.dart';

class GroupCard extends StatelessWidget {
  final String title;
  final double sliderValue;
  final List<ConfigItem> items;
  final Map<String, bool> checkValues;
  final ValueChanged<double> onSliderChanged;
  final ValueChanged<double> onSliderEnd;
  final Function(List<String>, bool) onCheckChanged;

  const GroupCard({
    super.key,
    required this.title,
    required this.sliderValue,
    required this.items,
    required this.checkValues,
    required this.onSliderChanged,
    required this.onSliderEnd,
    required this.onCheckChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 20, vertical: 8),
      elevation: 0,
      color: AppColors.surface,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(15),
        side: BorderSide(color: Colors.grey.shade200),
      ),
      child: ExpansionTile(
        shape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        collapsedShape: const RoundedRectangleBorder(side: BorderSide(color: Colors.transparent)),
        tilePadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        title: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Expanded(
              child: Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: AppColors.primary.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                sliderValue.toStringAsFixed(0),
                style: const TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold),
              ),
            ),
          ],
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 8.0),
          child: Slider(
            value: sliderValue,
            min: 0, max: 5, divisions: 5,
            activeColor: AppColors.primary,
            inactiveColor: AppColors.primary.withOpacity(0.1),
            onChanged: onSliderChanged,
            onChangeEnd: onSliderEnd,
          ),
        ),
        children: [
          const Padding(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Align(
              alignment: Alignment.centerLeft,
              child: Text(
                "(Desmarca las que no necesites)",
                style: TextStyle(fontSize: 12, color: Colors.grey, fontStyle: FontStyle.italic),
              ),
            ),
          ),
          ...items.map((item) {
            final isChecked = item.ids.every((id) => checkValues[id] == true);
            return CheckboxListTile(
              title: Text(item.label, style: const TextStyle(fontSize: 14)),
              value: isChecked,
              dense: true,
              activeColor: AppColors.primary,
              controlAffinity: ListTileControlAffinity.leading,
              onChanged: (bool? val) {
                if (val != null) onCheckChanged(item.ids, val);
              },
            );
          }).toList(),
          const SizedBox(height: 10),
        ],
      ),
    );
  }
}