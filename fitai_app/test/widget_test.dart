import 'package:flutter_test/flutter_test.dart';
import 'package:fitai_app/main.dart';

void main() {
  testWidgets('FitAI smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const FitAIApp());
    expect(find.text('FitAI - Teste'), findsOneWidget);
  });
}